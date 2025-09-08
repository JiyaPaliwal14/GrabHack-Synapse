import { useState, useCallback } from 'react';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'agent';
  timestamp: Date;
  type?: 'system' | 'action' | 'thought';
}

// Simulated agent tools and responses
const AGENT_TOOLS = {
  check_traffic: () => "🚦 Traffic Analysis: Heavy congestion detected on main route. Alternative route available with 15-minute delay.",
  get_merchant_status: () => "🏪 Merchant Status: Restaurant currently has 40-minute prep time due to high order volume.",
  contact_recipient: () => "📱 Contact Attempt: Recipient not answering phone. Voicemail left.",
  find_nearby_locker: () => "📦 Locker Search: Secure parcel locker found 0.3km away at Metro Station.",
  notify_customer: () => "📢 Customer Notification: Proactive alert sent with compensation voucher.",
  calculate_alternative_route: () => "🗺️ Route Calculation: New route calculated, +12 minutes but avoids accident zone.",
  initiate_mediation_flow: () => "⚖️ Mediation Started: Real-time resolution interface activated for both parties.",
  collect_evidence: () => "📸 Evidence Collection: Photos and questionnaire responses gathered from both parties."
};

const SCENARIO_RESPONSES = {
  "traffic": [
    { content: "🤔 Analyzing traffic disruption scenario...", type: 'thought' as const },
    { content: AGENT_TOOLS.check_traffic(), type: 'action' as const },
    { content: AGENT_TOOLS.calculate_alternative_route(), type: 'action' as const },
    { content: "✅ Resolution: Customer and driver notified of optimized route. ETA updated automatically.", type: 'system' as const }
  ],
  "merchant": [
    { content: "🤔 Evaluating merchant delay situation...", type: 'thought' as const },
    { content: AGENT_TOOLS.get_merchant_status(), type: 'action' as const },
    { content: AGENT_TOOLS.notify_customer(), type: 'action' as const },
    { content: "✅ Resolution: Customer informed proactively, voucher issued, driver reassigned to nearby delivery.", type: 'system' as const }
  ],
  "delivery": [
    { content: "🤔 Processing delivery availability issue...", type: 'thought' as const },
    { content: AGENT_TOOLS.contact_recipient(), type: 'action' as const },
    { content: AGENT_TOOLS.find_nearby_locker(), type: 'action' as const },
    { content: "✅ Resolution: Secure alternative delivery location identified and communicated to customer.", type: 'system' as const }
  ],
  "dispute": [
    { content: "🤔 Initiating real-time dispute resolution...", type: 'thought' as const },
    { content: AGENT_TOOLS.initiate_mediation_flow(), type: 'action' as const },
    { content: AGENT_TOOLS.collect_evidence(), type: 'action' as const },
    { content: "✅ Resolution: Evidence analyzed, fault determined, instant refund issued, driver exonerated.", type: 'system' as const }
  ]
};

export const useAgentLogic = () => {
  const [customerMessages, setCustomerMessages] = useState<Message[]>([]);
  const [operationsMessages, setOperationsMessages] = useState<Message[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  const addMessage = useCallback((
    type: 'customer' | 'operations',
    content: string,
    sender: 'user' | 'agent',
    messageType?: 'system' | 'action' | 'thought'
  ) => {
    const message: Message = {
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      content,
      sender,
      timestamp: new Date(),
      type: messageType
    };

    if (type === 'customer') {
      setCustomerMessages(prev => [...prev, message]);
    } else {
      setOperationsMessages(prev => [...prev, message]);
    }
  }, []);

  const processScenario = useCallback(async (scenario: string) => {
    setIsProcessing(true);
    
    // Determine scenario type based on keywords
    let scenarioType = 'delivery';
    if (scenario.toLowerCase().includes('traffic') || scenario.toLowerCase().includes('accident')) {
      scenarioType = 'traffic';
    } else if (scenario.toLowerCase().includes('merchant') || scenario.toLowerCase().includes('restaurant')) {
      scenarioType = 'merchant';
    } else if (scenario.toLowerCase().includes('dispute') || scenario.toLowerCase().includes('damage')) {
      scenarioType = 'dispute';
    }

    const responses = SCENARIO_RESPONSES[scenarioType as keyof typeof SCENARIO_RESPONSES];
    
    // Add responses with delays to simulate real agent thinking
    for (let i = 0; i < responses.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 1500));
      addMessage('operations', responses[i].content, 'agent', responses[i].type);
      
      // Also add to customer side for relevant updates
      if (responses[i].type === 'system') {
        await new Promise(resolve => setTimeout(resolve, 500));
        addMessage('customer', 
          `📱 Update: ${responses[i].content.replace('✅ Resolution: ', '')}`, 
          'agent', 'system'
        );
      }
    }
    
    setIsProcessing(false);
  }, [addMessage]);

  const handleCustomerMessage = useCallback((content: string) => {
    addMessage('customer', content, 'user');
    
    // Simple customer service responses
    setTimeout(() => {
      addMessage('customer', 
        "Thank you for contacting us! Our AI agent is processing your request and will provide updates shortly.", 
        'agent'
      );
    }, 1000);
  }, [addMessage]);

  const handleOperationsMessage = useCallback((content: string) => {
    addMessage('operations', content, 'user');
    processScenario(content);
  }, [addMessage, processScenario]);

  return {
    customerMessages,
    operationsMessages,
    isProcessing,
    handleCustomerMessage,
    handleOperationsMessage
  };
};