import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { Bot, Check, Copy, Languages } from "lucide-react";
import React, { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import {
  useAIState,
  useChannelStateContext,
  useMessageContext,
  useMessageTextStreaming,
} from "stream-chat-react";

const ChatMessage: React.FC = () => {
  const { message } = useMessageContext();
  const { channel } = useChannelStateContext();
  const { aiState } = useAIState(channel);

  const { streamedMessageText } = useMessageTextStreaming({
    text: message.text ?? "",
    renderingLetterCount: 10,
    streamingLetterIntervalMs: 50,
  });

  const isUser = !message.user?.id?.startsWith("ai-bot");
  
  // Load translation state from localStorage
  const getStoredTranslation = () => {
    try {
      const stored = localStorage.getItem(`translation_${message.id}`);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  };
  
  const storedTranslation = getStoredTranslation();
  const [translatedText, setTranslatedText] = useState<string | null>(storedTranslation?.translatedText || null);
  const [isTranslating, setIsTranslating] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState<string | null>(storedTranslation?.selectedLanguage || null);
  const [streamingTranslation, setStreamingTranslation] = useState("");
  const [copied, setCopied] = useState(false);

  // Persist translation state to localStorage
  useEffect(() => {
    if (translatedText !== null || selectedLanguage !== null) {
      localStorage.setItem(`translation_${message.id}`, JSON.stringify({
        translatedText,
        selectedLanguage,
      }));
    } else {
      localStorage.removeItem(`translation_${message.id}`);
    }
  }, [translatedText, selectedLanguage, message.id]);

  const copyToClipboard = async () => {
    if (message.text) {
      await navigator.clipboard.writeText(message.text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const translateText = async (targetLang: string) => {
    if (!message.text) return;
    
    // If the message looks like JSON (e.g., API responses), skip translation
    if (message.text.trim().startsWith('{') || message.text.trim().startsWith('[')) {
      setTranslatedText("Translation not available for this message type.");
      return;
    }
    
    // If the same language is selected again, clear the translation
    if (selectedLanguage === targetLang) {
      clearTranslation();
      return;
    }
    
    setIsTranslating(true);
    setSelectedLanguage(targetLang);
    setStreamingTranslation("");
    
    try {
      // Use POST request for longer texts to avoid URL length limits
      const response = await fetch('https://translate.googleapis.com/translate_a/single', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          client: 'gtx',
          sl: 'en',
          tl: targetLang,
          dt: 't',
          q: message.text,
        }),
      });
      
      const data = await response.json();
      
      // Check if the response is in the expected format
      if (!Array.isArray(data) || !Array.isArray(data[0])) {
        throw new Error("Invalid translation response format");
      }
      
      // Google Translate API returns array of arrays, collect all translated parts
      const fullTranslation = data[0]?.map((part: any[]) => part[0]).join('') || "";
      
      // Stream the translation like the AI response
      const words = fullTranslation.split(' ');
      let currentText = '';
      
      for (let i = 0; i < words.length; i++) {
        currentText += (i > 0 ? ' ' : '') + words[i];
        setStreamingTranslation(currentText);
        await new Promise(resolve => setTimeout(resolve, 50)); // 50ms delay between words
      }
      
      setTranslatedText(fullTranslation);
    } catch (error) {
      console.error("Translation failed:", error);
      setTranslatedText("Translation failed. Please try again.");
      setStreamingTranslation("Translation failed. Please try again.");
    } finally {
      setIsTranslating(false);
    }
  };

  const clearTranslation = () => {
    setTranslatedText(null);
    setStreamingTranslation("");
    setSelectedLanguage(null);
    localStorage.removeItem(`translation_${message.id}`);
  };

  const indianLanguages = [
    { code: "hi", name: "Hindi" },
    { code: "bn", name: "Bengali" },
    { code: "te", name: "Telugu" },
    { code: "mr", name: "Marathi" },
    { code: "ta", name: "Tamil" },
    { code: "ur", name: "Urdu" },
    { code: "gu", name: "Gujarati" },
    { code: "kn", name: "Kannada" },
    { code: "or", name: "Odia" },
    { code: "pa", name: "Punjabi" },
    { code: "as", name: "Assamese" },
    { code: "mai", name: "Maithili" },
    { code: "ml", name: "Malayalam" },
  ];

  const getAiStateMessage = () => {
    switch (aiState) {
      case "AI_STATE_THINKING":
        return "Thinking...";
      case "AI_STATE_GENERATING":
        return "Generating response...";
      case "AI_STATE_EXTERNAL_SOURCES":
        return "Accessing external sources...";
      case "AI_STATE_ERROR":
        return "An error occurred.";
      default:
        return null;
    }
  };

  const formatTime = (timestamp: string | Date) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div
      className={cn(
        "flex w-full mb-4 px-4 group",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <div
        className={cn(
          "flex max-w-[70%] sm:max-w-[60%] lg:max-w-[50%]",
          isUser ? "flex-row-reverse" : "flex-row"
        )}
      >
        {!isUser && (
          <div className="flex-shrink-0 mr-3 self-end">
            <Avatar className="h-8 w-8">
              <AvatarFallback className="bg-muted text-muted-foreground">
                <Bot className="h-4 w-4" />
              </AvatarFallback>
            </Avatar>
          </div>
        )}

        <div className="flex flex-col space-y-1">
          <div
            className={cn(
              "px-4 py-3 rounded-2xl text-sm leading-relaxed transition-all duration-200",
              isUser
                ? "str-chat__message-bubble str-chat__message-bubble--me rounded-br-md"
                : "str-chat__message-bubble rounded-bl-md"
            )}
          >
            <div className="break-words">
              <ReactMarkdown
                components={{
                  p: ({ children }) => (
                    <p className="mb-3 last:mb-0 leading-relaxed">{children}</p>
                  ),
                  code: ({ children, ...props }) => {
                    const { node, ...rest } = props;
                    const isInline = !rest.className?.includes("language-");

                    return isInline ? (
                      <code
                        className="px-1.5 py-0.5 rounded text-xs font-mono bg-black/10 dark:bg-white/10"
                        {...rest}
                      >
                        {children}
                      </code>
                    ) : (
                      <pre className="p-3 rounded-md overflow-x-auto my-2 text-xs font-mono bg-black/5 dark:bg-white/5">
                        <code {...rest}>{children}</code>
                      </pre>
                    );
                  },
                  ul: ({ children }) => (
                    <ul className="list-disc ml-4 mb-3 space-y-1">
                      {children}
                    </ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="list-decimal ml-4 mb-3 space-y-1">
                      {children}
                    </ol>
                  ),
                  li: ({ children }) => (
                    <li className="leading-relaxed">{children}</li>
                  ),
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-3 pl-3 my-2 italic border-current/30">
                      {children}
                    </blockquote>
                  ),
                  h1: ({ children }) => (
                    <h1 className="text-lg font-semibold mb-2 mt-4 first:mt-0">
                      {children}
                    </h1>
                  ),
                  h2: ({ children }) => (
                    <h2 className="text-base font-semibold mb-2 mt-3 first:mt-0">
                      {children}
                    </h2>
                  ),
                  h3: ({ children }) => (
                    <h3 className="text-sm font-semibold mb-2 mt-3 first:mt-0">
                      {children}
                    </h3>
                  ),
                  strong: ({ children }) => (
                    <strong className="font-semibold">{children}</strong>
                  ),
                  em: ({ children }) => <em className="italic">{children}</em>,
                }}
              >
                {streamedMessageText || message.text || ""}
              </ReactMarkdown>
              
              {translatedText && (
                <div className="mt-3 pt-3 border-t border-current/10">
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-xs text-muted-foreground">
                      Translation ({indianLanguages.find(l => l.code === selectedLanguage)?.name}):
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={clearTranslation}
                      className="h-5 px-2 text-xs hover:bg-muted/50 rounded"
                    >
                      Clear
                    </Button>
                  </div>
                  <div className="text-sm leading-relaxed">
                    {isTranslating ? (
                      <div className="space-y-2">
                        <Skeleton className="h-4 w-full" />
                        <Skeleton className="h-4 w-3/4" />
                        <Skeleton className="h-4 w-1/2" />
                      </div>
                    ) : (
                      <ReactMarkdown
                        components={{
                          p: ({ children }) => (
                            <p className="mb-3 last:mb-0 leading-relaxed">{children}</p>
                          ),
                          code: ({ children, ...props }) => {
                            const { node, ...rest } = props;
                            const isInline = !rest.className?.includes("language-");

                            return isInline ? (
                              <code
                                className="px-1.5 py-0.5 rounded text-xs font-mono bg-black/10 dark:bg-white/10"
                                {...rest}
                              >
                                {children}
                              </code>
                            ) : (
                              <pre className="p-3 rounded-md overflow-x-auto my-2 text-xs font-mono bg-black/5 dark:bg-white/5">
                                <code {...rest}>{children}</code>
                              </pre>
                            );
                          },
                          ul: ({ children }) => (
                            <ul className="list-disc ml-4 mb-3 space-y-1">
                              {children}
                            </ul>
                          ),
                          ol: ({ children }) => (
                            <ol className="list-decimal ml-4 mb-3 space-y-1">
                              {children}
                            </ol>
                          ),
                          li: ({ children }) => (
                            <li className="leading-relaxed">{children}</li>
                          ),
                          blockquote: ({ children }) => (
                            <blockquote className="border-l-3 pl-3 my-2 italic border-current/30">
                              {children}
                            </blockquote>
                          ),
                          h1: ({ children }) => (
                            <h1 className="text-lg font-semibold mb-2 mt-4 first:mt-0">
                              {children}
                            </h1>
                          ),
                          h2: ({ children }) => (
                            <h2 className="text-base font-semibold mb-2 mt-3 first:mt-0">
                              {children}
                            </h2>
                          ),
                          h3: ({ children }) => (
                            <h3 className="text-sm font-semibold mb-2 mt-3 first:mt-0">
                              {children}
                            </h3>
                          ),
                          strong: ({ children }) => (
                            <strong className="font-semibold">{children}</strong>
                          ),
                          em: ({ children }) => <em className="italic">{children}</em>,
                        }}
                      >
                        {translatedText}
                      </ReactMarkdown>
                    )}
                  </div>
                </div>
              )}
            </div>

            {aiState && !streamedMessageText && !message.text && (
              <div className="flex items-center gap-2 mt-2 pt-2">
                <span className="text-xs opacity-70">
                  {getAiStateMessage()}
                </span>
                <div className="flex space-x-1">
                  <div className="w-1 h-1 bg-current rounded-full typing-dot opacity-70"></div>
                  <div className="w-1 h-1 bg-current rounded-full typing-dot opacity-70"></div>
                  <div className="w-1 h-1 bg-current rounded-full typing-dot opacity-70"></div>
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center justify-between px-1">
            <span className="text-xs text-muted-foreground/70">
              {formatTime(message.created_at || new Date())}
            </span>

            {!isUser && !!message.text && (
              <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex gap-1">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 px-2 text-xs hover:bg-muted rounded-md"
                      disabled={isTranslating}
                    >
                      <Languages className="h-3 w-3 mr-1" />
                      <span>
                        {selectedLanguage 
                          ? indianLanguages.find(l => l.code === selectedLanguage)?.name 
                          : isTranslating 
                            ? "Translating..." 
                            : "Translate"
                        }
                      </span>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-40">
                    {indianLanguages.map((lang) => (
                      <DropdownMenuItem
                        key={lang.code}
                        onClick={() => translateText(lang.code)}
                        className={cn(
                          "text-xs flex items-center justify-between",
                          selectedLanguage === lang.code && "bg-accent"
                        )}
                      >
                        <span>{lang.name}</span>
                        {selectedLanguage === lang.code && (
                          <Check className="h-3 w-3 text-primary" />
                        )}
                      </DropdownMenuItem>
                    ))}
                    {selectedLanguage && (
                      <>
                        <div className="border-t my-1" />
                        <DropdownMenuItem
                          onClick={clearTranslation}
                          className="text-xs text-muted-foreground"
                        >
                          Clear Translation
                        </DropdownMenuItem>
                      </>
                    )}
                  </DropdownMenuContent>
                </DropdownMenu>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={copyToClipboard}
                  className="h-6 px-2 text-xs hover:bg-muted rounded-md"
                >
                  {copied ? (
                    <>
                      <Check className="h-3 w-3 mr-1 text-green-600" />
                      <span className="text-green-600">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-3 w-3 mr-1" />
                      <span>Copy</span>
                    </>
                  )}
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;
