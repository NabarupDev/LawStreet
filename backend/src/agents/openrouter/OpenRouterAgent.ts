import OpenAI from "openai";
import type { Channel, DefaultGenerics, Event, StreamChat } from "stream-chat";
import type { AIAgent } from "../types";
import { OpenRouterResponseHandler } from "./OpenRouterResponseHandler";

export class OpenRouterAgent implements AIAgent {
  private openai?: OpenAI;
  private assistant?: OpenAI.Beta.Assistants.Assistant;
  private openAiThread?: OpenAI.Beta.Threads.Thread;
  private lastInteractionTs = Date.now();

  private handlers: OpenRouterResponseHandler[] = [];

  constructor(
    readonly chatClient: StreamChat,
    readonly channel: Channel
  ) {}

  dispose = async () => {
    this.chatClient.off("message.new", this.handleMessage);
    await this.chatClient.disconnectUser();

    this.handlers.forEach((handler) => handler.dispose());
    this.handlers = [];
  };

  get user() {
    return this.chatClient.user;
  }

  getLastInteraction = (): number => this.lastInteractionTs;

  init = async () => {
    const apiKey = process.env.OPENROUTER_API_KEY as string | undefined;
    if (!apiKey) {
      throw new Error("OpenRouter API key is required");
    }

    this.openai = new OpenAI({
      apiKey,
      baseURL: "https://openrouter.ai/api/v1"
    });
    const model = process.env.OPENROUTER_MODEL || "anthropic/claude-3-haiku";
    this.assistant = await this.openai.beta.assistants.create({
      name: "AI Legal Assistant",
      instructions: this.getWritingAssistantPrompt(),
      model: model,
      tools: [
        {
          type: "function",
          function: {
            name: "web_search",
            description:
              "Search the web for current information, news, facts, or research on any topic",
            parameters: {
              type: "object",
              properties: {
                query: {
                  type: "string",
                  description: "The search query to find information about",
                },
              },
              required: ["query"],
            },
          },
        },
      ],
      temperature: 0.7,
    });
    this.openAiThread = await this.openai.beta.threads.create();

    this.chatClient.on("message.new", this.handleMessage);
  };

  private getWritingAssistantPrompt = (context?: string): string => {
    const currentDate = new Date().toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
    return `You are an expert AI Legal Assistant specializing in Indian Law. Your primary purpose is to provide accurate, helpful, and legally sound assistance on matters related to Indian laws, regulations, and legal procedures.

**Your Core Capabilities:**
- Legal Research, Analysis, and Advice on Indian Law.
- Interpretation of Indian statutes, case law, and legal principles.
- Guidance on legal procedures, rights, and obligations under Indian law.
- **Web Search**: You have the ability to search the web for up-to-date information using the 'web_search' tool.
- **Current Date**: Today's date is ${currentDate}. Please use this for any time-sensitive queries.

**Crucial Instructions:**
1. **ALWAYS answer questions related to Indian law, legal issues, or law-related topics.** Provide accurate and helpful information on Indian legal matters.
2. **Use the 'web_search' tool ONLY when the user asks for current information, news, recent legal developments, amendments, or facts that require up-to-date research.** Do not use it for standard legal definitions, sections of IPC/CrPC/CPC, or basic legal principles.
3. When you use the 'web_search' tool, you will receive a JSON object with search results. **You MUST base your response on the information provided in that search result.** Do not rely on your pre-existing knowledge for topics that require current information.
4. Synthesize the information from the web search to provide a comprehensive and accurate answer. Cite sources if the results include URLs.
5. Provide advice based on general legal principles and do not give personalized legal advice. Recommend consulting a qualified lawyer for specific cases.

**Response Format:**
- Be direct, accurate, and professional.
- Use clear formatting and legal terminology where appropriate.
- Never begin responses with phrases like "Here's the answer:", "Based on my knowledge:", or similar.
- Provide responses directly and cite relevant Indian laws, sections, or cases when applicable.

**Legal Context**: ${context || "General legal assistance under Indian law."}

Your goal is to provide reliable, current, and helpful legal information specifically related to Indian law. Failure to use web search for recent topics will result in an incorrect answer.`;
  };

  private handleMessage = async (e: Event<DefaultGenerics>) => {
    if (!this.openai || !this.openAiThread || !this.assistant) {
      console.log("OpenRouter not initialized");
      return;
    }

    if (!e.message || e.message.ai_generated) {
      return;
    }

    const message = e.message.text;
    if (!message) return;

    this.lastInteractionTs = Date.now();

    const writingTask = (e.message.custom as { writingTask?: string })
      ?.writingTask;
    const context = writingTask ? `Writing Task: ${writingTask}` : undefined;
    const instructions = this.getWritingAssistantPrompt(context);

    await this.openai.beta.threads.messages.create(this.openAiThread.id, {
      role: "user",
      content: message,
    });

    const { message: channelMessage } = await this.channel.sendMessage({
      text: "",
      ai_generated: true,
    });

    await this.channel.sendEvent({
      type: "ai_indicator.update",
      ai_state: "AI_STATE_THINKING",
      cid: channelMessage.cid,
      message_id: channelMessage.id,
    });

    const run = this.openai.beta.threads.runs.createAndStream(
      this.openAiThread.id,
      {
        assistant_id: this.assistant.id,
      }
    );

    const handler = new OpenRouterResponseHandler(
      this.openai,
      this.openAiThread,
      run,
      this.chatClient,
      this.channel,
      channelMessage,
      () => this.removeHandler(handler)
    );
    this.handlers.push(handler);
    void handler.run();
  };

  private removeHandler = (handlerToRemove: OpenRouterResponseHandler) => {
    this.handlers = this.handlers.filter(
      (handler) => handler !== handlerToRemove
    );
  };
}