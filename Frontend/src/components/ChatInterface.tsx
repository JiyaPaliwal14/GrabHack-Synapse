import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Send, Bot, User, Settings, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'agent';
  timestamp: Date;
  type?: 'system' | 'action' | 'thought';
}

interface ChatInterfaceProps {
  type: 'customer' | 'operations';
  title: string;
  placeholder: string;
  messages: Message[];
  onSendMessage: (content: string) => void;
  isProcessing?: boolean;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  type,
  title,
  placeholder,
  messages,
  onSendMessage,
  isProcessing = false,
}) => {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && !isProcessing) {
      onSendMessage(inputValue.trim());
      setInputValue('');
    }
  };

  const getMessageVariant = (message: Message) => {
    if (message.sender === 'user') return 'user';
    return message.type || 'agent';
  };

  const getMessageIcon = (message: Message) => {
    if (message.sender === 'user') return <User className="w-4 h-4" />;
    if (message.type === 'action') return <Zap className="w-4 h-4" />;
    if (message.type === 'system') return <Settings className="w-4 h-4" />;
    return <Bot className="w-4 h-4" />;
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className={cn(
        "p-4 border-b bg-gradient-to-r text-white",
        type === 'customer' 
          ? "from-synapse-customer to-synapse-primary" 
          : "from-synapse-ops to-slate-600"
      )}>
        <h2 className="text-lg font-semibold">{title}</h2>
        <p className="text-sm opacity-90">
          {type === 'customer' 
            ? "Customer support interface" 
            : "Operations command center"}
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gradient-to-b from-background to-muted/20">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            <div className="text-center">
              <Bot className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>Start a conversation...</p>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "flex gap-3",
                message.sender === 'user' ? "justify-end" : "justify-start"
              )}
            >
              {message.sender === 'agent' && (
                <div className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center text-white flex-shrink-0",
                  message.type === 'action' && "bg-synapse-secondary",
                  message.type === 'system' && "bg-synapse-warning",
                  !message.type && type === 'customer' && "bg-synapse-customer",
                  !message.type && type === 'operations' && "bg-synapse-ops"
                )}>
                  {getMessageIcon(message)}
                </div>
              )}
              
              <Card className={cn(
                "max-w-[80%] p-3 shadow-sm",
                message.sender === 'user' 
                  ? "bg-primary text-primary-foreground ml-auto" 
                  : "bg-card",
                message.type === 'action' && "border-synapse-secondary/50 bg-synapse-secondary/5",
                message.type === 'system' && "border-synapse-warning/50 bg-synapse-warning/5",
                message.type === 'thought' && "border-muted bg-muted/30 italic"
              )}>
                <div className="text-sm leading-relaxed whitespace-pre-wrap">
                  {message.content}
                </div>
                <div className="text-xs opacity-70 mt-2">
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </Card>

              {message.sender === 'user' && (
                <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground flex-shrink-0">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))
        )}
        
        {isProcessing && (
          <div className="flex gap-3">
            <div className={cn(
              "w-8 h-8 rounded-full flex items-center justify-center text-white",
              type === 'customer' ? "bg-synapse-customer" : "bg-synapse-ops"
            )}>
              <Bot className="w-4 h-4" />
            </div>
            <Card className="bg-card p-3 shadow-sm">
              <div className="flex items-center gap-2">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
                <span className="text-sm text-muted-foreground">Agent is thinking...</span>
              </div>
            </Card>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t bg-card">
        <div className="flex gap-2">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={placeholder}
            disabled={isProcessing}
            className="flex-1"
          />
          <Button 
            type="submit" 
            disabled={!inputValue.trim() || isProcessing}
            className={cn(
              type === 'customer' 
                ? "bg-synapse-customer hover:bg-synapse-customer/90" 
                : "bg-synapse-ops hover:bg-synapse-ops/90"
            )}
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </form>
    </div>
  );
};