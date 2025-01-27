import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Upload, Linkedin, FileText, AlertCircle } from 'lucide-react';

const LearningRecommendationInterface = () => {
  const [step, setStep] = useState(1);
  const [userData, setUserData] = useState({
    careerGoal: '',
    skillSource: 'manual', // 'manual', 'resume', 'linkedin'
    resumeFile: null,
    linkedInUrl: '',
    manualSkills: '',
    processingStatus: ''
  });

  const [fileError, setFileError] = useState('');

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file && (file.type === 'application/pdf' || file.type === 'application/msword' || 
        file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')) {
      setUserData(prev => ({
        ...prev,
        resumeFile: file,
        skillSource: 'resume'
      }));
      setFileError('');
    } else {
      setFileError('Please upload a PDF or Word document');
    }
  };

  const handleLinkedInSubmit = (url) => {
    if (url.includes('linkedin.com/')) {
      setUserData(prev => ({
        ...prev,
        linkedInUrl: url,
        skillSource: 'linkedin'
      }));
      setFileError('');
    } else {
      setFileError('Please enter a valid LinkedIn URL');
    }
  };

  const renderSkillSourceSelection = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Button
          variant={userData.skillSource === 'resume' ? 'default' : 'outline'}
          className="h-24 flex flex-col items-center justify-center space-y-2"
          onClick={() => document.getElementById('resumeUpload').click()}
        >
          <Upload className="w-6 h-6" />
          <span>Upload Resume</span>
          <input
            id="resumeUpload"
            type="file"
            className="hidden"
            accept=".pdf,.doc,.docx"
            onChange={handleFileUpload}
          />
        </Button>

        <Button
          variant={userData.skillSource === 'linkedin' ? 'default' : 'outline'}
          className="h-24 flex flex-col items-center justify-center space-y-2"
          onClick={() => setUserData(prev => ({ ...prev, skillSource: 'linkedin' }))}
        >
          <Linkedin className="w-6 h-6" />
          <span>LinkedIn Profile</span>
        </Button>

        <Button
          variant={userData.skillSource === 'manual' ? 'default' : 'outline'}
          className="h-24 flex flex-col items-center justify-center space-y-2"
          onClick={() => setUserData(prev => ({ ...prev, skillSource: 'manual' }))}
        >
          <FileText className="w-6 h-6" />
          <span>Enter Manually</span>
        </Button>
      </div>

      {fileError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{fileError}</AlertDescription>
        </Alert>
      )}

      {userData.skillSource === 'linkedin' && (
        <div className="space-y-2">
          <Input
            placeholder="Paste your LinkedIn profile URL"
            value={userData.linkedInUrl}
            onChange={(e) => setUserData(prev => ({ ...prev, linkedInUrl: e.target.value }))}
            onBlur={(e) => handleLinkedInSubmit(e.target.value)}
          />
        </div>
      )}

      {userData.skillSource === 'manual' && (
        <Textarea
          placeholder="List your current skills, technologies, and experiences..."
          className="h-32"
          value={userData.manualSkills}
          onChange={(e) => setUserData(prev => ({ ...prev, manualSkills: e.target.value }))}
        />
      )}
    </div>
  );

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Career-Based Learning Recommendations</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Target Career Path</h3>
            <Input
              placeholder="Enter your target role (e.g., Data Scientist, Full Stack Developer)"
              value={userData.careerGoal}
              onChange={(e) => setUserData(prev => ({ ...prev, careerGoal: e.target.value }))}
            />
          </div>

          <div className="space-y-4">
            <h3 className="text-lg font-medium">Skills Assessment</h3>
            {renderSkillSourceSelection()}
          </div>

          <Button
            className="w-full"
            disabled={!userData.careerGoal || 
              (userData.skillSource === 'manual' && !userData.manualSkills) ||
              (userData.skillSource === 'linkedin' && !userData.linkedInUrl) ||
              (userData.skillSource === 'resume' && !userData.resumeFile)}
            onClick={() => {/* Handle submission */}}
          >
            Analyze Skills & Generate Recommendations
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default LearningRecommendationInterface;
