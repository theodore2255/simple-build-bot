import { Brain, Upload, Search, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

export const HeroSection = () => {
  const features = [
    {
      icon: Upload,
      title: "Document Ingestion",
      description: "Upload up to 20 documents with intelligent chunking and processing"
    },
    {
      icon: Brain,
      title: "Vector Embeddings",
      description: "Advanced text embeddings stored in high-performance vector database"
    },
    {
      icon: Search,
      title: "Smart Retrieval",
      description: "Contextual document chunk retrieval for accurate query responses"
    },
    {
      icon: Zap,
      title: "LLM Integration",
      description: "Powered by state-of-the-art language models for intelligent responses"
    }
  ];

  return (
    <div className="relative bg-gradient-subtle border-b">
      <div className="absolute inset-0 bg-gradient-hero opacity-5" />
      <div className="relative max-w-6xl mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 bg-primary/10 text-primary px-4 py-2 rounded-full text-sm font-medium mb-6">
            <Brain className="w-4 h-4" />
            Advanced RAG Pipeline
          </div>
          <h1 className="text-5xl font-bold mb-6 bg-gradient-hero bg-clip-text text-transparent">
            Intelligent Document Processing
          </h1>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto mb-8">
            Upload your documents and ask intelligent questions. Our Retrieval-Augmented Generation 
            pipeline combines document search with AI to provide accurate, contextual responses.
          </p>
          <div className="flex gap-4 justify-center">
            <Button variant="hero" size="xl">
              Get Started
            </Button>
            <Button variant="outline" size="xl">
              Learn More
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <Card
                key={index}
                className="p-6 text-center hover:shadow-elegant transition-all duration-300 hover:scale-105 bg-card/50 backdrop-blur-sm"
              >
                <div className="w-12 h-12 bg-gradient-primary rounded-lg mx-auto mb-4 flex items-center justify-center">
                  <Icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="font-semibold mb-2">{feature.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
};