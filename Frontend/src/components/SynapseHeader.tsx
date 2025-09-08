import React from 'react';
import { Brain, Zap, Activity, BarChart3 } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';

export const SynapseHeader: React.FC = () => {
  return (
    <div className="bg-gradient-to-r from-background via-muted/30 to-background border-b p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-gradient-to-br from-synapse-primary to-synapse-secondary rounded-xl flex items-center justify-center shadow-lg">
              <Brain className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-synapse-primary to-synapse-secondary bg-clip-text text-transparent">
                Project Synapse
              </h1>
              <p className="text-sm text-muted-foreground">
                Agentic Last-Mile Delivery Coordinator
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Link to="/">
                <Button variant="ghost" size="sm">
                  Chat Interface
                </Button>
              </Link>
              <Link to="/dashboard">
                <Button variant="ghost" size="sm" className="flex items-center gap-2">
                  <BarChart3 className="w-4 h-4" />
                  Dashboard
                </Button>
              </Link>
            </div>
            
            <Card className="p-3 bg-synapse-success/10 border-synapse-success/20">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-synapse-success" />
                <span className="text-sm font-medium text-synapse-success">
                  Agent Active
                </span>
              </div>
            </Card>
            
            <Card className="p-3 bg-synapse-secondary/10 border-synapse-secondary/20">
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-synapse-secondary" />
                <span className="text-sm font-medium text-synapse-secondary">
                  Real-time Processing
                </span>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};