import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  Download, Mail, Copy, ExternalLink, Star, 
  Filter, SortAsc, Grid, List 
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu';

const CourseRecommendations = () => {
  const [viewMode, setViewMode] = useState('grid');
  const [sortBy, setSortBy] = useState('relevance');
  const [filterProvider, setFilterProvider] = useState('all');
  const [emailAddress, setEmailAddress] = useState('');
  const [recommendations] = useState([
    {
      title: "Sample Course 1",
      provider: "Coursera",
      rating: 4.5,
      description: "Learn the fundamentals of programming",
      skills: ["Python", "Data Structures"],
      price: 49.99,
      duration: "6 weeks",
      image_url: null
    },
    {
      title: "Sample Course 2",
      provider: "Udemy",
      rating: 4.7,
      description: "Advanced machine learning concepts",
      skills: ["ML", "AI"],
      price: 59.99,
      duration: "8 weeks",
      image_url: null
    }
  ]);
  const [skillGaps] = useState({
    "Technical Skills": ["Python", "Machine Learning"],
    "Tools": ["Git", "Docker"],
    "Concepts": ["Algorithms", "Data Structures"]
  });

  const formatPrice = (price) => {
    if (typeof price === 'number') {
      return `$${price.toFixed(2)}`;
    }
    return price;
  };

  const handleEmailRecommendations = () => {
    console.log('Sending recommendations to:', emailAddress);
  };

  const handleDownloadPDF = () => {
    console.log('Downloading PDF');
  };

  const handleCopyToClipboard = async () => {
    const text = JSON.stringify(recommendations, null, 2);
    await navigator.clipboard.writeText(text);
  };

  const CourseCard = ({ course }) => (
    <Card className={`${viewMode === 'grid' ? 'w-full' : 'w-full mb-4'}`}>
      <CardContent className="p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="w-full md:w-48 h-32 bg-gray-100 rounded-md overflow-hidden">
            <img 
              src={course.image_url || "/api/placeholder/192/128"} 
              alt={course.title}
              className="w-full h-full object-cover"
            />
          </div>
          <div className="flex-1">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-lg font-semibold">{course.title}</h3>
                <p className="text-sm text-gray-500">{course.provider}</p>
              </div>
              <div className="flex items-center space-x-2">
                {course.rating && (
                  <div className="flex items-center">
                    <Star className="w-4 h-4 text-yellow-400 fill-current" />
                    <span className="ml-1">{course.rating}</span>
                  </div>
                )}
                <Button variant="outline" size="sm">
                  <ExternalLink className="w-4 h-4 mr-2" />
                  Visit
                </Button>
              </div>
            </div>
            <p className="mt-2 text-sm text-gray-600 line-clamp-2">
              {course.description}
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              {course.skills?.map((skill, index) => (
                <span 
                  key={index}
                  className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                >
                  {skill}
                </span>
              ))}
            </div>
            <div className="mt-2 flex justify-between items-center">
              <span className="text-sm font-medium">
                {formatPrice(course.price)}
              </span>
              <span className="text-sm text-gray-500">
                {course.duration || 'Self-paced'}
              </span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="max-w-7xl mx-auto p-4 space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Personalized Course Recommendations</h2>
        <div className="flex space-x-2">
          <Button variant="outline" onClick={handleDownloadPDF}>
            <Download className="w-4 h-4 mr-2" />
            Download PDF
          </Button>
          <Button variant="outline" onClick={handleCopyToClipboard}>
            <Copy className="w-4 h-4 mr-2" />
            Copy
          </Button>
          <div className="flex items-center space-x-2 border rounded-md p-2">
            <Input
              type="email"
              placeholder="Enter email"
              value={emailAddress}
              onChange={(e) => setEmailAddress(e.target.value)}
              className="w-48"
            />
            <Button onClick={handleEmailRecommendations}>
              <Mail className="w-4 h-4 mr-2" />
              Send
            </Button>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex space-x-2">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                <Filter className="w-4 h-4 mr-2" />
                Filter
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem onClick={() => setFilterProvider('all')}>
                All Providers
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setFilterProvider('coursera')}>
                Coursera
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setFilterProvider('udemy')}>
                Udemy
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setFilterProvider('edx')}>
                EdX
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                <SortAsc className="w-4 h-4 mr-2" />
                Sort
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem onClick={() => setSortBy('relevance')}>
                Relevance
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setSortBy('rating')}>
                Rating
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setSortBy('price')}>
                Price
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        <div className="flex space-x-2">
          <Button
            variant={viewMode === 'grid' ? 'default' : 'outline'}
            onClick={() => setViewMode('grid')}
          >
            <Grid className="w-4 h-4" />
          </Button>
          <Button
            variant={viewMode === 'list' ? 'default' : 'outline'}
            onClick={() => setViewMode('list')}
          >
            <List className="w-4 h-4" />
          </Button>
        </div>
      </div>

      <Tabs defaultValue="all">
        <TabsList>
          <TabsTrigger value="all">All Recommendations</TabsTrigger>
          {Object.keys(skillGaps).map((category) => (
            <TabsTrigger key={category} value={category}>
              {category}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="all" className="mt-6">
          <div className={`grid ${viewMode === 'grid' ? 'grid-cols-1 md:grid-cols-2 gap-4' : 'grid-cols-1 gap-2'}`}>
            {recommendations.map((course, index) => (
              <CourseCard key={index} course={course} />
            ))}
          </div>
        </TabsContent>

        {Object.entries(skillGaps).map(([category, gaps]) => (
          <TabsContent key={category} value={category} className="mt-6">
            <div className={`grid ${viewMode === 'grid' ? 'grid-cols-1 md:grid-cols-2 gap-4' : 'grid-cols-1 gap-2'}`}>
              {recommendations
                .filter(course => course.skills?.some(skill => gaps.includes(skill)))
                .map((course, index) => (
                  <CourseCard key={index} course={course} />
                ))}
            </div>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
};

export default CourseRecommendations;
