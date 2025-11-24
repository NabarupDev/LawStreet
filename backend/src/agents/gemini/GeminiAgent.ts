import { GoogleGenerativeAI } from "@google/generative-ai";
import type { Channel, DefaultGenerics, Event, StreamChat } from "stream-chat";
import type { AIAgent } from "../types";
import { GeminiResponseHandler } from "./GeminiResponseHandler";

export class GeminiAgent implements AIAgent {
  private lastInteractionTs = Date.now();
  private conversationHistory: Array<{ role: "user" | "model"; parts: string }> = [];
  private genAI: GoogleGenerativeAI;
  private model: any;

  constructor(
    readonly chatClient: StreamChat,
    readonly channel: Channel
  ) {
    const apiKey = process.env.GEMINI_API_KEY || "AIzaSyAup9S-1oRi-eNsbkIsxruWS9B6aAP2BTA";
    this.genAI = new GoogleGenerativeAI(apiKey);
    this.model = this.genAI.getGenerativeModel({ 
      model: "gemini-1.5-flash",
      tools: [{
        functionDeclarations: [{
          name: "web_search",
          description: "Search the web for information",
          parameters: {
            type: "object",
            properties: {
              query: { type: "string", description: "The search query" }
            },
            required: ["query"]
          }
        }]
      }] as any
    });
  }

  dispose = async () => {
    this.chatClient.off("message.new", this.handleMessage);
    await this.chatClient.disconnectUser();
    this.conversationHistory = [];
  };

  get user() {
    return this.chatClient.user;
  }

  getLastInteraction = (): number => this.lastInteractionTs;

  init = async () => {
    // Test connection to Gemini API
    try {
      await this.model.generateContent("Hello");
      console.log("Successfully connected to Gemini API");
    } catch (error) {
      console.warn("Warning: Could not connect to Gemini API. Check your API key.");
    }

    this.chatClient.on("message.new", this.handleMessage);
  };

  private getWritingAssistantPrompt = (context?: string): string => {
    const currentDate = new Date().toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
    return `You are an Expert AI Legal Assistant specializing in Indian Law.

Your duties:
- Provide accurate, fact-based information about Indian laws, acts, statutes, rights, legal processes, and general legal principles.
- Use clear, simple language.
- If the user’s issue involves private disputes (like landlord–tenant issues), explain the relevant legal framework and general steps.
- DO NOT give personalized legal advice, legal interpretations, or guaranteed outcomes.
- Recommend consulting a qualified Indian lawyer for any personal, actionable, or case-specific guidance.

Tools:
- Use the "web_search" tool ONLY when the user asks for recent updates, judgments, notifications, or changes in law.
- Always cite sources when using search results.

Safety:
- If a user request is outside Indian law, tell them politely.
- Do not create fake laws or citations.
- Do not draft binding legal documents (e.g., legal notices, petitions) — provide only sample formats.

Current date: ${currentDate}

Context:
${context || "General Indian legal assistance."}
`;
  };

  private handleMessage = async (e: Event<DefaultGenerics>) => {
    if (!e.message || e.message.ai_generated) {
      return;
    }

    const message = e.message.text;
    if (!message) return;

    this.lastInteractionTs = Date.now();

    this.conversationHistory.push({
      role: "user",
      parts: message,
    });

    const writingTask = (e.message.custom as { writingTask?: string })
      ?.writingTask;
    const context = writingTask ? `Writing Task: ${writingTask}` : undefined;
    const instructions = this.getWritingAssistantPrompt(context);

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

    const chat = this.model.startChat({
      history: [
        { role: 'user', parts: [{ text: instructions }] },
        { role: 'model', parts: [{ text: 'Understood. I will assist with Indian law questions accurately and professionally.' }] },
        ...this.conversationHistory.slice(0, -1).map(h => ({
          role: h.role,
          parts: [{ text: h.parts }],
        })),
      ],
    });

    const handler = new GeminiResponseHandler(this.genAI, chat, this.chatClient, this.channel, channelMessage, () => {
      this.conversationHistory.push({
        role: "model",
        parts: handler.getMessageText(),
      });
      if (this.conversationHistory.length > 10) {
        this.conversationHistory = this.conversationHistory.slice(-10);
      }
    });

    await handler.run();
  };
}