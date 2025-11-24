import { StreamChat } from "stream-chat";
import { apiKey, serverClient } from "../serverClient";
import { OllamaAgent } from "./ollama/OllamaAgent";
import { GeminiAgent } from "./gemini/GeminiAgent";
import { OpenRouterAgent } from "./openrouter/OpenRouterAgent";
import { AgentPlatform, AIAgent } from "./types";

export const createAgent = async (
  user_id: string,
  platform: AgentPlatform,
  channel_type: string,
  channel_id: string
): Promise<AIAgent> => {
  const token = serverClient.createToken(user_id);
  const chatClient = new StreamChat(apiKey, undefined, {
    allowServerSideConnect: true,
  });

  await chatClient.connectUser({ id: user_id }, token);
  const channel = chatClient.channel(channel_type, channel_id);
  await channel.watch();

  switch (platform) {
    case AgentPlatform.WRITING_ASSISTANT:
    case AgentPlatform.OPENAI:
      return new OpenRouterAgent(chatClient, channel);
    case AgentPlatform.GEMINI:
      return new GeminiAgent(chatClient, channel);
    case AgentPlatform.OPENROUTER:
      return new OpenRouterAgent(chatClient, channel);
    default:
      throw new Error(`Unsupported agent platform: ${platform}`);
  }
};
