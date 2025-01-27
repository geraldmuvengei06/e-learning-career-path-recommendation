import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { BookOpen, Briefcase, GraduationCap, Upload, Linkedin, FileText } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

const LearningRecommendationInterface = () => {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [skillSource, setSkillSource] = useState('manual'); // 'manual', 'resume', 'linkedin'
  const [userData, setUserData] = useState({
    careerGoals: '',
    currentSkills: '',
    linkedInUrl: '',
    resumeFile: null,
    extractedSkills: null
  });

  const handleInputChange = (field, value) => {
    setUserData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (file) {
      setLoading(true);
      try {
        const formData = new FormData();
        formData.append('resume', file);
        
        // Simulated API call to parse resume
        // Replace with actual API endpoint
        const response = await fetch('/api/parse-resume', {
          method: 'POST',
          body: formData
        });
        
        const data = await response.json();
        setUserData(prev => ({
          ...prev,
          resumeFile: file,
          extractedSkills: data.skills
        }));
        setSkillSource('resume');
      } catch (error) {
        console.error('Error parsing resume:', error);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleLinkedInExtraction = async () => {
    if (!userData.linkedInUrl) return;
    
    setLoading(true);
    try {
      // Simulated API call to extract LinkedIn data
      const response = await fetch('/api/extract-linkedin', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url: userData.linkedInUrl })
      });
      
      const data = await response.json();
      setUserData(prev => ({
        ...prev,
        extractedSkills: data.skills
      }));
      setSkillSource('linkedin');
    } catch (error) {
      console.error('Error extracting LinkedIn data:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderSkillsSection = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
        </div>
      );
    }

    return (
      <div className="space-y-4">
        <div className="flex space-x-4">
          <Button
            variant={skillSource === 'manual' ? 'default' : 'outline'}
            onClick={() => setSkillSource('manual')}
          >
            <FileText className="w-4 h-4 mr-2" />
            Manual Entry
          </Button>
          <Button
            variant={skillSource === 'resume' ? 'default' : 'outline'}
            onClick={() => setSkillSource('resume')}
          >
            <Upload className="w-4 h-4 mr-2" />
            Upload Resume
          </Button>
          <Button
            variant={skillSource === 'linkedin' ? 'default' : 'outline'}
            onClick={() => setSkillSource('linkedin')}
          >
            <Linkedin className="w-4 h-4 mr-2" />
            LinkedIn
          </Button>
        </div>

        {skillSource === 'manual' && (
          <Textarea 
            placeholder="List your current technical and soft skills..."
            className="h-32"
            value={userData.currentSkills}
            onChange={(e) => handleInputChange('currentSkills', e.target.value)}
          />
        )}

        {skillSource === 'resume' && (
          <div className="space-y-4">
            <Input
              type="file"
              accept=".pdf,.doc,.docx"
              onChange={handleFileUpload}
            />
            {userData.extractedSkills && (
              <Alert>
                <AlertDescription>
                  Skills extracted from resume: {userData.extractedSkills.join(', ')}
                </AlertDescription>
              </Alert>
            )}
          </div>
        )}

        {skillSource === 'linkedin' && (
          <div className="space-y-4">
            <Input 
              placeholder="LinkedIn Profile URL"
              value={userData.linkedInUrl}
              onChange={(e) => handleInputChange('linkedInUrl', e.target.value)}
            />
            <Button onClick={handleLinkedInExtraction}>
              Extract Skills
            </Button>
            {userData.extractedSkills && (
              <Alert>
                <AlertDescription>
                  Skills extracted from LinkedIn: {userData.extractedSkills.join(', ')}
                </AlertDescription>
              </Alert>
            )}
          </div>
        )}
      </div>
    );
  };

  const renderStep = () => {
    switch(step) {
      case 1:
        return (
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <GraduationCap className="w-6 h-6 text-blue-500" />
              <h3 className="text-lg font-medium">Career Goals</h3>
            </div>
            <Textarea 
              placeholder="What specific role or position are you targeting? (e.g., Data Scientist, Full Stack Developer)"
              className="h-32"
              value={userData.careerGoals}
              onChange={(e) => handleInputChange('careerGoals', e.target.value)}
            />
          </div>
        );
      
      case 2:
        return (
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <BookOpen className="w-6 h-6 text-green-500" />
              <h3 className="text-lg font-medium">Skills Assessment</h3>
            </div>
            {renderSkillsSection()}
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Personalized Learning Recommendations</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          <div className="flex justify-between mb-8">
            {[1, 2].map((num) => (
              <div 
                key={num}
                className={`w-8 h-8 rounded-full flex items-center justify-center
                  ${step >= num ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
              >
                {num}
              </div>
            ))}
          </div>

          {renderStep()}

          <div className="flex justify-between mt-6">
            {step > 1 && (
              <Button
                variant="outline"
                onClick={() => setStep(prev => prev - 1)}
              >
                Back
              </Button>
            )}
            <Button
              className={step === 1 ? 'ml-auto' : ''}
              onClick={() => step === 2 ? null : setStep(prev => prev + 1)}
            >
              {step === 2 ? 'Get Recommendations' : 'Next'}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default LearningRecommendationInterface;
