import axios from "axios";
import type { Channel, DefaultGenerics, Event, StreamChat } from "stream-chat";
import type { AIAgent } from "../types";

export class OllamaAgent implements AIAgent {
  private lastInteractionTs = Date.now();
  private conversationHistory: Array<{ role: string; content: string }> = [];
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
      await axios.get(`${this.llmApiUrl}/health`, { timeout: 5000 });
      console.log("Successfully connected to LLM service");
    } catch (error) {
      console.warn(
        "Warning: Could not connect to LLM service. Make sure the FastAPI server is running."
      );
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

    try {
      const response = await axios.post(
        `${this.llmApiUrl}/ask`,
        {
          query: message,
        },
        {
          timeout: 120000,
        }
      );

      const answer = response.data.answer;
      const sources = response.data.sources || [];

      this.conversationHistory.push({
        role: "assistant",
        content: answer,
      });

      if (this.conversationHistory.length > 10) {
        this.conversationHistory = this.conversationHistory.slice(-10);
      }

      let formattedAnswer = answer;
      if (sources.length > 0) {
        formattedAnswer += "\n\n**Sources:**\n";
        sources.forEach((source: any, index: number) => {
          formattedAnswer += `${index + 1}. ${source.source} - Section ${source.section}\n`;
        });
      }

      await this.chatClient.partialUpdateMessage(channelMessage.id, {
        set: {
          text: formattedAnswer,
        },
      });

      await this.channel.sendEvent({
        type: "ai_indicator.clear",
        cid: channelMessage.cid,
        message_id: channelMessage.id,
      });
    } catch (error) {
      console.error("Error calling LLM service:", error);

      let errorMessage = "Sorry, I encountered an error processing your request.";
      if (axios.isAxiosError(error)) {
        if (error.code === "ECONNREFUSED") {
          errorMessage =
            "Could not connect to the LLM service. Please ensure the FastAPI server is running on " +
            this.llmApiUrl;
        } else if (error.response) {
          errorMessage = `LLM service error: ${error.response.data?.detail || error.response.statusText}`;
        } else if (error.request) {
          errorMessage = "No response from LLM service. The request timed out.";
        }
      }

      await this.chatClient.partialUpdateMessage(channelMessage.id, {
        set: {
          text: errorMessage,
        },
      });

      await this.channel.sendEvent({
        type: "ai_indicator.clear",
        cid: channelMessage.cid,
        message_id: channelMessage.id,
      });
    }
  };
}
