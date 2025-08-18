import { FileText, Calendar, Eye, Trash2, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

interface Document {
  id: string;
  name: string;
  size: string;
  uploadDate: Date;
  pages: number;
  chunks: number;
  status: 'processed' | 'processing' | 'error';
}

export const DocumentLibrary = () => {
  const documents: Document[] = [
    {
      id: '1',
      name: 'RAG_System_Overview.pdf',
      size: '2.4 MB',
      uploadDate: new Date(2024, 0, 15),
      pages: 12,
      chunks: 48,
      status: 'processed'
    },
    {
      id: '2',
      name: 'LLM_Best_Practices.docx',
      size: '1.8 MB',
      uploadDate: new Date(2024, 0, 14),
      pages: 8,
      chunks: 32,
      status: 'processed'
    },
    {
      id: '3',
      name: 'Vector_Database_Guide.txt',
      size: '0.5 MB',
      uploadDate: new Date(2024, 0, 13),
      pages: 3,
      chunks: 12,
      status: 'processing'
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'processed':
        return 'bg-success text-success-foreground';
      case 'processing':
        return 'bg-primary text-primary-foreground';
      case 'error':
        return 'bg-destructive text-destructive-foreground';
      default:
        return 'bg-muted text-muted-foreground';
    }
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString([], { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold">Document Library</h3>
        <Badge variant="secondary" className="text-sm">
          {documents.length} documents
        </Badge>
      </div>

      <div className="border rounded-lg overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[40px]"></TableHead>
              <TableHead>Document</TableHead>
              <TableHead>Size</TableHead>
              <TableHead>Upload Date</TableHead>
              <TableHead>Pages</TableHead>
              <TableHead>Chunks</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="w-[120px]">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {documents.map((doc) => (
              <TableRow key={doc.id} className="hover:bg-muted/30">
                <TableCell>
                  <FileText className="w-5 h-5 text-primary" />
                </TableCell>
                <TableCell>
                  <div className="font-medium">{doc.name}</div>
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {doc.size}
                </TableCell>
                <TableCell className="text-muted-foreground">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4" />
                    {formatDate(doc.uploadDate)}
                  </div>
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {doc.pages}
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {doc.chunks}
                </TableCell>
                <TableCell>
                  <Badge className={getStatusColor(doc.status)}>
                    {doc.status}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div className="flex gap-1">
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                      <Eye className="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                      <Download className="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive hover:text-destructive">
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4 bg-muted/30">
          <div className="text-2xl font-bold text-primary">156</div>
          <div className="text-sm text-muted-foreground">Total Chunks</div>
        </Card>
        <Card className="p-4 bg-muted/30">
          <div className="text-2xl font-bold text-accent">4.7 MB</div>
          <div className="text-sm text-muted-foreground">Storage Used</div>
        </Card>
        <Card className="p-4 bg-muted/30">
          <div className="text-2xl font-bold text-success">23</div>
          <div className="text-sm text-muted-foreground">Total Pages</div>
        </Card>
      </div>
    </Card>
  );
};