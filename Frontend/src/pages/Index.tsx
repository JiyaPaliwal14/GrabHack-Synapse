import React from 'react';
import { SynapseHeader } from '@/components/SynapseHeader';
import { ChatInterface } from '@/components/ChatInterface';
import { useAgentLogic } from '@/hooks/useAgentLogic';

const Index = () => {
  const {
    customerMessages,
    operationsMessages,
    isProcessing,
    handleCustomerMessage,
    handleOperationsMessage
  } = useAgentLogic();

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-muted/10 to-background">
      <SynapseHeader />
      
      <div className="h-[calc(100vh-120px)] flex">
        {/* Customer Interface */}
        <div className="flex-1 border-r">
          <ChatInterface
            type="customer"
            title="Customer Support"
            placeholder="Describe your delivery issue..."
            messages={customerMessages}
            onSendMessage={handleCustomerMessage}
            isProcessing={false}
          />
        </div>
        
        {/* Operations Interface */}
        <div className="flex-1">
          <ChatInterface
            type="operations"
            title="Operations Command Center"
            placeholder="Input delivery scenario (e.g., 'Traffic accident on Route 101, customer going to airport')"
            messages={operationsMessages}
            onSendMessage={handleOperationsMessage}
            isProcessing={isProcessing}
          />
        </div>
      </div>
    </div>
  );
};

export default Index;
