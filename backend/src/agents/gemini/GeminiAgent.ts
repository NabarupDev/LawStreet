import axios from "axios";
import type { Channel, DefaultGenerics, Event, StreamChat } from "stream-chat";
import type { AIAgent } from "../types";
import { GeminiResponseHandler } from "./GeminiResponseHandler";

export class GeminiAgent implements AIAgent {
  private lastInteractionTs = Date.now();
  private conversationHistory: Array<{ role: "user" | "model"; parts: string }> = [];
  private llmApiUrl: string;

  constructor(
    readonly chatClient: StreamChat,
    readonly channel: Channel
  ) {
    this.llmApiUrl = process.env.LLM_API_URL || "http://localhost:8000";
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
    // Test connection to LLM service
    try {
      const response = await axios.get(`${this.llmApiUrl}/health`, { timeout: 5000 });
      console.log("Successfully connected to LLM service:", response.data);
    } catch (error) {
      console.warn("Warning: Could not connect to LLM service at", this.llmApiUrl);
      console.warn("Make sure the Python FastAPI server is running.");
    }

    this.chatClient.on("message.new", this.handleMessage);
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

    const handler = new GeminiResponseHandler(
      this.llmApiUrl,
      this.chatClient,
      this.channel,
      channelMessage,
      message,
      () => {
        this.conversationHistory.push({
          role: "model",
          parts: handler.getMessageText(),
        });
        if (this.conversationHistory.length > 10) {
          this.conversationHistory = this.conversationHistory.slice(-10);
        }
      }
    );

    await handler.run();
  };
}