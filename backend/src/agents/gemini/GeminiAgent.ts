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
      model: "gemini-1.5-pro-latest",
      tools: [{
        functionDeclarations: [{
          name: "web_search",
          description: "Search the web for information when you need to look up current or additional details not in your training data",
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
    // This prompt is designed to be direct and clear for the AI model.
    return `
You are an expert AI Legal Assistant for Indian Law. Your primary role is to provide accurate and relevant information based on the user's questions about Indian legal topics.

**Core Instructions:**

1.  **Analyze the User's Question:** Carefully read the user's query and provide a direct answer. Do not provide information on unrelated legal topics.
2.  **Scope of Knowledge:** Your expertise is limited to Indian Law. This includes the Indian Penal Code (IPC), Criminal Procedure Code (CrPC), Civil Procedure Code (CPC), the Constitution of India, and other Indian statutes. If the question is outside this scope, politely decline to answer.
3.  **Your Identity:** When asked "who are you" or about your identity, describe yourself as an "AI Legal Assistant specializing in Indian Law."
4.  **No Legal Advice:** Do NOT provide personalized legal advice, opinions, or predict outcomes of legal cases. Always end your responses with a disclaimer recommending consultation with a qualified Indian lawyer for specific legal problems.
5.  **Use of Tools:** Use the 'web_search' tool ONLY when the user asks for very recent legal updates, new amendments, or current events that are not part of your core training data. Do not use it for general legal principles.
6.  **Clarity:** Explain legal concepts in simple and clear language.

**Current Date:** ${currentDate}
${context ? `\n**Specific Task Context:** ${context}` : ""}
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

    const chat = this.genAI.getGenerativeModel({ 
      model: "gemini-1.5-pro-latest",
      tools: [{
        functionDeclarations: [{
          name: "web_search",
          description: "Search the web for information when you need to look up current or additional details not in your training data",
          parameters: {
            type: "object",
            properties: {
              query: { type: "string", description: "The search query" }
            },
            required: ["query"]
          }
        }]
      }] as any
    }).startChat({
      history: [
        { role: 'user', parts: [{ text: instructions }] },
        { role: 'model', parts: [{ text: 'Understood. I am ready to assist with Indian law questions.' }] }
      ]
    });

    const handler = new GeminiResponseHandler(this.genAI, chat, this.chatClient, this.channel, channelMessage, message, () => {
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