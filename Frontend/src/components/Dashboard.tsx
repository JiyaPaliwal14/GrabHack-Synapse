import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Clock, MessageCircle, CheckCircle, AlertTriangle, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

interface ConversationHistory {
  id: string;
  date: string;
  scenario: string;
  status: 'resolved' | 'in-progress' | 'escalated';
  messages: number;
  resolution: string;
  tools_used: string[];
}

const mockConversations: ConversationHistory[] = [
  {
    id: 'conv-001',
    date: '2024-01-08 14:30',
    scenario: 'Traffic accident blocking main route, urgent airport trip',
    status: 'resolved',
    messages: 8,
    resolution: 'Alternative route calculated, passenger notified, ETA updated',
    tools_used: ['check_traffic', 'calculate_alternative_route', 'notify_passenger_and_driver']
  },
  {
    id: 'conv-002',
    date: '2024-01-08 13:15',
    scenario: 'Restaurant delay 40 minutes, customer ordered food',
    status: 'resolved',
    messages: 12,
    resolution: 'Customer notified with voucher, driver reassigned to nearby delivery',
    tools_used: ['get_merchant_status', 'notify_customer', 'reassign_driver']
  },
  {
    id: 'conv-003',
    date: '2024-01-08 12:45',
    scenario: 'Package delivery failed, recipient unavailable',
    status: 'resolved',
    messages: 6,
    resolution: 'Secure locker found and arranged for alternative delivery',
    tools_used: ['contact_recipient', 'find_nearby_locker']
  },
  {
    id: 'conv-004',
    date: '2024-01-08 11:20',
    scenario: 'Damaged item dispute at customer doorstep',
    status: 'resolved',
    messages: 15,
    resolution: 'Evidence analyzed, instant refund issued, driver exonerated',
    tools_used: ['initiate_mediation_flow', 'collect_evidence', 'analyze_evidence', 'issue_instant_refund']
  },
  {
    id: 'conv-005',
    date: '2024-01-08 10:30',
    scenario: 'Merchant location incorrect in system',
    status: 'in-progress',
    messages: 4,
    resolution: 'Investigation ongoing',
    tools_used: ['verify_merchant_location', 'contact_merchant']
  }
];

const Dashboard = () => {
  const [selectedConversation, setSelectedConversation] = useState<ConversationHistory | null>(null);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'resolved':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'in-progress':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'escalated':
        return <AlertTriangle className="h-4 w-4 text-red-500" />;
      default:
        return <MessageCircle className="h-4 w-4" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants = {
      'resolved': 'default',
      'in-progress': 'secondary',
      'escalated': 'destructive'
    } as const;
    
    return (
      <Badge variant={variants[status as keyof typeof variants] || 'outline'}>
        {status.replace('-', ' ')}
      </Badge>
    );
  };

  const stats = {
    total: mockConversations.length,
    resolved: mockConversations.filter(c => c.status === 'resolved').length,
    inProgress: mockConversations.filter(c => c.status === 'in-progress').length,
    avgMessages: Math.round(mockConversations.reduce((acc, c) => acc + c.messages, 0) / mockConversations.length)
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/">
              <Button variant="outline" size="sm" className="flex items-center gap-2">
                <ArrowLeft className="h-4 w-4" />
                Back to Chat
              </Button>
            </Link>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Agent Dashboard</h1>
              <p className="text-muted-foreground">Monitor conversation history and agent performance</p>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Conversations</CardTitle>
              <MessageCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total}</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Resolved</CardTitle>
              <CheckCircle className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{stats.resolved}</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">In Progress</CardTitle>
              <Clock className="h-4 w-4 text-yellow-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-yellow-600">{stats.inProgress}</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Messages</CardTitle>
              <MessageCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.avgMessages}</div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <Tabs defaultValue="conversations" className="space-y-4">
          <TabsList>
            <TabsTrigger value="conversations">Conversation History</TabsTrigger>
            <TabsTrigger value="details">Conversation Details</TabsTrigger>
          </TabsList>
          
          <TabsContent value="conversations" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Recent Conversations</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date/Time</TableHead>
                      <TableHead>Scenario</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Messages</TableHead>
                      <TableHead>Tools Used</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {mockConversations.map((conversation) => (
                      <TableRow key={conversation.id}>
                        <TableCell className="font-mono text-sm">
                          {conversation.date}
                        </TableCell>
                        <TableCell className="max-w-xs truncate">
                          {conversation.scenario}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            {getStatusIcon(conversation.status)}
                            {getStatusBadge(conversation.status)}
                          </div>
                        </TableCell>
                        <TableCell>{conversation.messages}</TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {conversation.tools_used.slice(0, 2).map((tool) => (
                              <Badge key={tool} variant="outline" className="text-xs">
                                {tool.replace('_', ' ')}
                              </Badge>
                            ))}
                            {conversation.tools_used.length > 2 && (
                              <Badge variant="outline" className="text-xs">
                                +{conversation.tools_used.length - 2}
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => setSelectedConversation(conversation)}
                          >
                            View Details
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="details" className="space-y-4">
            {selectedConversation ? (
              <Card>
                <CardHeader>
                  <CardTitle>Conversation Details - {selectedConversation.id}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Date & Time</label>
                      <p className="font-mono">{selectedConversation.date}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Status</label>
                      <div className="flex items-center gap-2 mt-1">
                        {getStatusIcon(selectedConversation.status)}
                        {getStatusBadge(selectedConversation.status)}
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Scenario</label>
                    <p className="mt-1">{selectedConversation.scenario}</p>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Resolution</label>
                    <p className="mt-1">{selectedConversation.resolution}</p>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Tools Used</label>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {selectedConversation.tools_used.map((tool) => (
                        <Badge key={tool} variant="secondary">
                          {tool.replace('_', ' ')}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Message Count</label>
                    <p className="mt-1">{selectedConversation.messages} messages exchanged</p>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="text-center py-8">
                  <MessageCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">Select a conversation from the history tab to view details</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Dashboard;