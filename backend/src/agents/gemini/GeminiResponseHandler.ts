import axios from "axios";
import type { Channel, MessageResponse, StreamChat } from "stream-chat";

export class GeminiResponseHandler {
  private message_text = "";
  private is_done = false;
  private last_update_time = 0;

  constructor(
    private readonly llmApiUrl: string,
    private readonly chatClient: StreamChat,
    private readonly channel: Channel,
    private readonly message: MessageResponse,
    private readonly userMessage: string,
    private readonly onDispose: () => void
  ) {
    this.chatClient.on("ai_indicator.stop", this.handleStopGenerating);
  }

  getMessageText = () => this.message_text;

  run = async () => {
    try {
      console.log(`Calling LLM service at ${this.llmApiUrl}/ask with query:`, this.userMessage);
      
      // Call the LLM service
      const response = await axios.post(
        `${this.llmApiUrl}/ask`,
        { query: this.userMessage },
        { timeout: 120000 } // 120 second timeout
      );

      if (!response.data || !response.data.answer) {
        throw new Error("Invalid response from LLM service");
      }

      const answer = response.data.answer;
      const sources = response.data.sources || [];

      console.log(`Received answer from LLM service (length: ${answer.length})`);

      // Simulate streaming by breaking the answer into chunks
      const chunkSize = 50; // Characters per chunk
      const chunks = [];
      for (let i = 0; i < answer.length; i += chunkSize) {
        chunks.push(answer.substring(i, i + chunkSize));
      }

      // Stream the response
      for (const chunk of chunks) {
        if (this.is_done) break;

        if (this.message_text.length + chunk.length > 4900) {
          const remainingSpace = 4900 - this.message_text.length;
          this.message_text += chunk.substring(0, remainingSpace) + "... (response truncated due to length limit)";
          this.updateMessage(true);
          this.is_done = true;
          break;
        } else {
          this.message_text += chunk;
          this.updateMessage();
          // Small delay to simulate streaming
          await new Promise(resolve => setTimeout(resolve, 50));
        }
      }

      // Add sources to the response if available
      if (sources.length > 0 && !this.is_done) {
        let sourcesText = "\n\n**Sources:**\n";
        sources.forEach((source: any, index: number) => {
          sourcesText += `${index + 1}. ${source.source} - Section ${source.section}\n`;
        });
        
        if (this.message_text.length + sourcesText.length <= 4900) {
          this.message_text += sourcesText;
        }
      }

      // Final update
      this.updateMessage(true);
      await this.channel.sendEvent({
        type: "ai_indicator.clear",
        cid: this.message.cid,
        message_id: this.message.id,
      });
    } catch (error) {
      await this.handleError(error as Error);
    } finally {
      await this.dispose();
    }
  };

  dispose = async () => {
    if (this.is_done) return;
    this.is_done = true;
    this.chatClient.off("ai_indicator.stop", this.handleStopGenerating);
    this.onDispose();
  };

  private handleStopGenerating = async (event: any) => {
    if (this.is_done || event.message_id !== this.message.id) return;
    await this.channel.sendEvent({
      type: "ai_indicator.clear",
      cid: this.message.cid,
      message_id: this.message.id,
    });
    await this.dispose();
  };

  private updateMessage = (final = false) => {
    const now = Date.now();
    if (final || now - this.last_update_time > 1000) {
      let textToUpdate = this.message_text;
      if (textToUpdate.length > 4900) {
        textToUpdate = textToUpdate.substring(0, 4900) + "... (response truncated due to length limit)";
      }
      this.chatClient.partialUpdateMessage(this.message.id, {
        set: { text: textToUpdate }
      });
      this.last_update_time = now;
    }
  };

  private handleError = async (error: Error) => {
    console.log('Error in GeminiResponseHandler:', error.message, error.stack);
    if (this.is_done) return;
    await this.channel.sendEvent({
      type: "ai_indicator.update",
      ai_state: "AI_STATE_ERROR",
      cid: this.message.cid,
      message_id: this.message.id,
    });
    await this.chatClient.partialUpdateMessage(this.message.id, {
      set: {
        text: error.message ?? "Error generating the message",
      },
    });
    await this.dispose();
  };

}