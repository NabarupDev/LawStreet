import { GoogleGenerativeAI } from "@google/generative-ai";
import type { Channel, MessageResponse, StreamChat } from "stream-chat";

export class GeminiResponseHandler {
  private message_text = "";
  private is_done = false;
  private last_update_time = 0;

  constructor(
    private readonly genAI: GoogleGenerativeAI,
    private readonly chat: any,
    private readonly chatClient: StreamChat,
    private readonly channel: Channel,
    private readonly message: MessageResponse,
    private readonly onDispose: () => void
  ) {
    this.chatClient.on("ai_indicator.stop", this.handleStopGenerating);
  }

  getMessageText = () => this.message_text;

  run = async () => {
    try {
      const result = await this.chat.sendMessageStream(this.message.text);
      if (!result.stream) throw new Error("Failed to get stream from Gemini API");

      let functionCalls: any[] = [];

      for await (const chunk of result.stream) {
        if (this.is_done) break;
        const candidates = chunk.candidates;
        if (candidates) {
          for (const candidate of candidates) {
            const content = candidate.content;
            if (content && content.parts) {
              for (const part of content.parts) {
                if (part.text) {
                  if (this.message_text.length + part.text.length > 4900) {
                    const remainingSpace = 4900 - this.message_text.length;
                    this.message_text += part.text.substring(0, remainingSpace) + "... (response truncated due to length limit)";
                    this.updateMessage(true);
                    this.is_done = true;
                    break;
                  } else {
                    this.message_text += part.text;
                    this.updateMessage();
                  }
                }
                if (part.functionCall) {
                  functionCalls.push(part.functionCall);
                }
              }
            }
          }
        }
      }

      if (functionCalls.length > 0 && !this.is_done) {
        await this.channel.sendEvent({
          type: "ai_indicator.update",
          ai_state: "AI_STATE_EXTERNAL_SOURCES",
          cid: this.message.cid,
          message_id: this.message.id,
        });
        const toolResponses = [];
        for (const call of functionCalls) {
          if (call.name === 'web_search') {
            const searchResult = await this.performWebSearch(call.args.query);
            toolResponses.push({
              functionResponse: {
                name: call.name,
                response: { result: searchResult }
              }
            });
          }
        }
        // send the tool response as a new message to the chat
        const toolMessage = {
          role: 'user',
          parts: toolResponses
        };
        const result2 = await this.chat.sendMessageStream(toolMessage);
        if (!result2.stream) throw new Error("Failed to get stream from Gemini API after tool call");

        for await (const chunk of result2.stream) {
          if (this.is_done) break;
          const candidates = chunk.candidates;
          if (candidates) {
            for (const candidate of candidates) {
              const content = candidate.content;
              if (content && content.parts) {
                for (const part of content.parts) {
                  if (part.text) {
                    if (this.message_text.length + part.text.length > 4900) {
                      const remainingSpace = 4900 - this.message_text.length;
                      this.message_text += part.text.substring(0, remainingSpace) + "... (response truncated due to length limit)";
                      this.updateMessage(true);
                      this.is_done = true;
                      break;
                    } else {
                      this.message_text += part.text;
                      this.updateMessage();
                    }
                  }
                  // assuming no more function calls
                }
              }
            }
          }
        }
      }

      // final update
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

  private performWebSearch = async (query: string): Promise<string> => {
    const TAVILY_API_KEY = process.env.TAVILY_API_KEY;

    if (!TAVILY_API_KEY) {
      return JSON.stringify({
        error: "Web search is not available. API key not configured.",
      });
    }

    console.log(`Performing web search for: "${query}"`);

    try {
      const response = await fetch("https://api.tavily.com/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${TAVILY_API_KEY}`,
        },
        body: JSON.stringify({
          query: query,
          search_depth: "advanced",
          max_results: 5,
          include_answer: true,
          include_raw_content: false,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`Tavily search failed for query "${query}":`, errorText);
        return JSON.stringify({
          error: `Search failed with status: ${response.status}`,
          details: errorText,
        });
      }

      const data = await response.json();
      console.log(`Tavily search successful for query "${query}"`);

      return JSON.stringify(data);
    } catch (error) {
      console.error(
        `An exception occurred during web search for "${query}":`,
        error
      );
      return JSON.stringify({
        error: "An exception occurred during the search.",
        message: error instanceof Error ? error.message : "Unknown error",
      });
    }
  };
}