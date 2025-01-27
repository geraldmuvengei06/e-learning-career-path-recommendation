import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { BookOpen, Briefcase, GraduationCap } from 'lucide-react';

const LearningRecommendationInterface = () => {
  const [step, setStep] = useState(1);
  const [userData, setUserData] = useState({
    careerGoals: '',
    currentSkills: '',
    linkedInUrl: '',
    preferredLearningStyle: ''
  });

  const handleInputChange = (field, value) => {
    setUserData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleNext = () => {
    setStep(prev => prev + 1);
  };

  const handleBack = () => {
    setStep(prev => prev - 1);
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
              placeholder="What are your career goals? Where do you see yourself in 2-3 years?"
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
              <h3 className="text-lg font-medium">Current Skills</h3>
            </div>
            <Textarea 
              placeholder="List your current technical and soft skills..."
              className="h-32"
              value={userData.currentSkills}
              onChange={(e) => handleInputChange('currentSkills', e.target.value)}
            />
          </div>
        );
      
      case 3:
        return (
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <Briefcase className="w-6 h-6 text-purple-500" />
              <h3 className="text-lg font-medium">Professional Profile</h3>
            </div>
            <Input 
              placeholder="LinkedIn Profile URL (optional)"
              value={userData.linkedInUrl}
              onChange={(e) => handleInputChange('linkedInUrl', e.target.value)}
            />
            <Textarea 
              placeholder="What's your preferred learning style? (e.g., video courses, interactive projects, reading)"
              className="h-32"
              value={userData.preferredLearningStyle}
              onChange={(e) => handleInputChange('preferredLearningStyle', e.target.value)}
            />
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
          {/* Progress Indicator */}
          <div className="flex justify-between mb-8">
            {[1, 2, 3].map((num) => (
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
                onClick={handleBack}
              >
                Back
              </Button>
            )}
            <Button
              className={step === 1 ? 'ml-auto' : ''}
              onClick={handleNext}
            >
              {step === 3 ? 'Get Recommendations' : 'Next'}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default LearningRecommendationInterface;
