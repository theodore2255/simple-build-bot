import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { HeroSection } from '@/components/HeroSection';
import { DocumentUpload } from '@/components/DocumentUpload';
import { QueryInterface } from '@/components/QueryInterface';
import { DocumentLibrary } from '@/components/DocumentLibrary';

const Index = () => {
  const [activeTab, setActiveTab] = useState('upload');

  return (
    <div className="min-h-screen bg-gradient-subtle">
      <HeroSection />
      
      <div className="max-w-6xl mx-auto px-6 py-12">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-8">
            <TabsTrigger value="upload" className="text-sm font-medium">
              Document Upload
            </TabsTrigger>
            <TabsTrigger value="query" className="text-sm font-medium">
              Query Interface
            </TabsTrigger>
            <TabsTrigger value="library" className="text-sm font-medium">
              Document Library
            </TabsTrigger>
          </TabsList>

          <TabsContent value="upload" className="space-y-6">
            <DocumentUpload />
          </TabsContent>

          <TabsContent value="query" className="space-y-6">
            <QueryInterface />
          </TabsContent>

          <TabsContent value="library" className="space-y-6">
            <DocumentLibrary />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Index;
