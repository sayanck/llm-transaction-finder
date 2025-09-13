import React, { useState, useEffect } from 'react';
import { Brain, AlertTriangle, CheckCircle, Clock, Users, Target, TrendingUp } from 'lucide-react';
import { AnalysisResult, ApiResponse } from '../types';
import { apiService } from '../services/api';
import LoadingSpinner from './LoadingSpinner';
import RiskBadge from './RiskBadge';

const AIAnalysis: React.FC = () => {
  const [analysisData, setAnalysisData] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    // Don't auto-load analysis on mount - let user trigger it
  }, []);

  const startAnalysis = async () => {
    try {
      setAnalyzing(true);
      setLoading(true);
      setError(null);
      
      // Use progressive analysis for better performance
      const response: ApiResponse<AnalysisResult> = await apiService.analyzePatternsProgressive();
      setAnalysisData(response.data);
      
      if (response.mock) {
        setError('Using mock analysis - configure GEMINI_API_KEY for real AI analysis');
      } else if (response.partial) {
        setError('Using cached analysis due to processing limitations');
      } else if (response.cached) {
        setError('Using cached analysis from previous run');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to analyze patterns';
      setError(errorMessage);
      
      // If it's a timeout error, provide more helpful message
      if (errorMessage.includes('timeout')) {
        setError('Analysis is taking longer than expected. This may be due to large dataset size. Please try again or contact support if the issue persists.');
      }
    } finally {
      setLoading(false);
      setAnalyzing(false);
    }
  };

  const renderExecutiveSummary = () => {
    if (!analysisData?.overall_assessment) return null;

    const assessment = analysisData.overall_assessment;
    
    return (
      <div className="card mb-6">
        <div className="card-header">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900 flex items-center">
              <Target className="w-5 h-5 mr-2" />
              Executive Summary
            </h3>
            <RiskBadge level={assessment.overall_risk_level} />
          </div>
        </div>
        <div className="card-content">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 mb-4 sm:mb-6">
            <div className="bg-blue-50 rounded-lg p-3 sm:p-4">
              <div className="flex items-center">
                <AlertTriangle className="h-6 w-6 sm:h-8 sm:w-8 text-blue-600 flex-shrink-0" />
                <div className="ml-2 sm:ml-3 min-w-0">
                  <p className="text-xs sm:text-sm font-medium text-blue-900">Total Threats</p>
                  <p className="text-lg sm:text-2xl font-semibold text-blue-900">{assessment.total_threads}</p>
                </div>
              </div>
            </div>
            
            <div className="bg-green-50 rounded-lg p-3 sm:p-4">
              <div className="flex items-center">
                <CheckCircle className="h-6 w-6 sm:h-8 sm:w-8 text-green-600 flex-shrink-0" />
                <div className="ml-2 sm:ml-3 min-w-0">
                  <p className="text-xs sm:text-sm font-medium text-green-900">Patterns Analyzed</p>
                  <p className="text-lg sm:text-2xl font-semibold text-green-900">
                    {Object.keys(assessment.pattern_summary).length}
                  </p>
                </div>
              </div>
            </div>
            
            <div className="bg-purple-50 rounded-lg p-3 sm:p-4 sm:col-span-2 lg:col-span-1">
              <div className="flex items-center">
                <TrendingUp className="h-6 w-6 sm:h-8 sm:w-8 text-purple-600 flex-shrink-0" />
                <div className="ml-2 sm:ml-3 min-w-0">
                  <p className="text-xs sm:text-sm font-medium text-purple-900">Risk Level</p>
                  <p className="text-lg sm:text-2xl font-semibold text-purple-900 capitalize">
                    {assessment.overall_risk_level}
                  </p>
                </div>
              </div>
            </div>
          </div>
          
          <div className="bg-gray-50 rounded-lg p-3 sm:p-4">
            <h4 className="font-medium text-gray-900 mb-2 text-sm sm:text-base">AI Assessment</h4>
            <p className="text-xs sm:text-sm text-gray-700 leading-relaxed break-words">{assessment.executive_summary}</p>
          </div>
        </div>
      </div>
    );
  };

  const renderPatternSummary = () => {
    if (!analysisData?.overall_assessment?.pattern_summary) return null;

    const patterns = analysisData.overall_assessment.pattern_summary;
    
    return (
      <div className="card mb-6">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">Pattern Analysis Summary</h3>
        </div>
        <div className="card-content">
          <div className="space-y-3 sm:space-y-4">
            {Object.entries(patterns).map(([patternType, summary]) => (
              <div key={patternType} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="min-w-0 flex-1">
                  <h4 className="font-medium text-gray-900 capitalize text-sm sm:text-base truncate">
                    {patternType.replace('_', ' ')}
                  </h4>
                  <p className="text-xs sm:text-sm text-gray-600">
                    {summary.thread_count} suspicious threads identified
                  </p>
                </div>
                <div className="ml-2 flex-shrink-0">
                  <RiskBadge level={summary.risk_level} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderTopThreats = () => {
    if (!analysisData?.overall_assessment?.top_threats?.length) return null;

    const threats = analysisData.overall_assessment.top_threats;
    
    return (
      <div className="card mb-6">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">Top Threats</h3>
        </div>
        <div className="card-content">
          <div className="space-y-3 sm:space-y-4">
            {threats.map((thread, index) => (
              <div key={thread.thread_id} className="border rounded-lg p-3 sm:p-4">
                <div className="flex items-start justify-between mb-2 sm:mb-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center mb-2">
                      <span className="bg-red-100 text-red-800 text-xs font-medium px-2 py-1 rounded-full mr-2 flex-shrink-0">
                        #{index + 1}
                      </span>
                      <h4 className="font-medium text-gray-900 text-sm sm:text-base break-words">{thread.description}</h4>
                    </div>
                    {thread.participants.length > 0 && (
                      <div className="flex items-center text-xs sm:text-sm text-gray-600 mb-2">
                        <Users className="w-3 h-3 sm:w-4 sm:h-4 mr-1 flex-shrink-0" />
                        <span className="truncate">{thread.participants.join(', ')}</span>
                      </div>
                    )}
                  </div>
                  <div className="ml-2 flex-shrink-0">
                    <RiskBadge level={thread.risk_level} />
                  </div>
                </div>
                
                {thread.evidence.length > 0 && (
                  <div className="mb-2 sm:mb-3">
                    <h5 className="text-xs sm:text-sm font-medium text-gray-700 mb-1">Evidence:</h5>
                    <ul className="list-disc list-inside text-xs sm:text-sm text-gray-600 space-y-1">
                      {thread.evidence.map((evidence, evidenceIndex) => (
                        <li key={evidenceIndex} className="break-words">{evidence}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                <div className="space-y-2">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between text-xs sm:text-sm space-y-1 sm:space-y-0">
                    <span className="text-gray-500">
                      Potential Violation: <span className="font-medium break-words">{thread.potential_violation}</span>
                    </span>
                    {thread.transactions_involved.length > 0 && (
                      <span className="text-gray-500">
                        {thread.transactions_involved.length} transactions involved
                      </span>
                    )}
                  </div>
                  
                  {thread.confidence_score && (
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between text-xs sm:text-sm space-y-1 sm:space-y-0">
                      <span className="text-gray-500">
                        Confidence: <span className="font-medium">{(thread.confidence_score * 100).toFixed(0)}%</span>
                      </span>
                      <div className="w-full sm:w-16 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full" 
                          style={{ width: `${thread.confidence_score * 100}%` }}
                        ></div>
                      </div>
                    </div>
                  )}
                  
                  {thread.recommended_action && (
                    <div className="text-xs sm:text-sm">
                      <span className="text-gray-500">Recommended Action: </span>
                      <span className="font-medium text-blue-700 break-words">{thread.recommended_action}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderDetailedAnalysis = () => {
    if (!analysisData) return null;

    const patternTypes = ['frequent_pairs', 'round_amounts', 'high_activity_periods', 'repeated_amounts', 'quick_successive'];
    
    return (
      <div className="space-y-6">
        {patternTypes.map((patternType) => {
          const analysis = analysisData[patternType as keyof AnalysisResult];
          if (!analysis || typeof analysis !== 'object' || !('threads' in analysis)) return null;

          return (
            <div key={patternType} className="card">
              <div className="card-header">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium text-gray-900 capitalize">
                    {patternType.replace('_', ' ')} Analysis
                  </h3>
                  <RiskBadge level={analysis.risk_level} />
                </div>
              </div>
              <div className="card-content">
                <p className="text-gray-600 mb-4">{analysis.summary}</p>
                
                {analysis.key_insights && analysis.key_insights.length > 0 && (
                  <div className="mb-4 p-3 bg-blue-50 rounded-lg">
                    <h5 className="text-sm font-medium text-blue-900 mb-2">Key Insights:</h5>
                    <ul className="list-disc list-inside text-sm text-blue-800 space-y-1">
                      {analysis.key_insights.map((insight, index) => (
                        <li key={index}>{insight}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {analysis.threads.length > 0 ? (
                  <div className="space-y-3">
                    {analysis.threads.map((thread, index) => (
                      <div key={thread.thread_id} className="bg-gray-50 rounded-lg p-4">
                        <div className="flex items-start justify-between mb-2">
                          <h4 className="font-medium text-gray-900">{thread.description}</h4>
                          <RiskBadge level={thread.risk_level} size="sm" />
                        </div>
                        
                        {thread.participants.length > 0 && (
                          <div className="flex items-center text-sm text-gray-600 mb-2">
                            <Users className="w-4 h-4 mr-1" />
                            {thread.participants.join(', ')}
                          </div>
                        )}
                        
                        {thread.evidence.length > 0 && (
                          <div className="mb-2">
                            <details className="cursor-pointer">
                              <summary className="text-sm font-medium text-gray-700">
                                View Evidence ({thread.evidence.length} items)
                              </summary>
                              <ul className="mt-2 list-disc list-inside text-sm text-gray-600 space-y-1">
                                {thread.evidence.map((evidence, evidenceIndex) => (
                                  <li key={evidenceIndex}>{evidence}</li>
                                ))}
                              </ul>
                            </details>
                          </div>
                        )}
                        
                        <div className="space-y-1">
                          <div className="text-xs text-gray-500">
                            Potential Violation: {thread.potential_violation}
                          </div>
                          {thread.confidence_score && (
                            <div className="text-xs text-gray-500">
                              Confidence: {(thread.confidence_score * 100).toFixed(0)}%
                            </div>
                          )}
                          {thread.recommended_action && (
                            <div className="text-xs text-blue-600">
                              Action: {thread.recommended_action}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 italic">No suspicious threads identified in this pattern.</p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="p-3 sm:p-4 lg:p-6">
        <LoadingSpinner text={analyzing ? "AI is analyzing transaction patterns..." : "Loading analysis results..."} />
        {analyzing && (
          <div className="mt-3 sm:mt-4 text-center">
            <p className="text-xs sm:text-sm text-gray-600 mb-2">This may take up to 3 minutes for large datasets</p>
            <div className="flex items-center justify-center space-x-2 text-xs sm:text-sm text-gray-500">
              <Brain className="w-3 h-3 sm:w-4 sm:h-4 animate-pulse" />
              <span>LLM is running</span>
            </div>
            <div className="mt-2 sm:mt-3 text-xs text-gray-400 space-y-1">
              <p>• Analyzing patterns </p>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="p-3 sm:p-4 lg:p-6 space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center space-y-3 sm:space-y-0">
        <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-gray-900 flex items-center">
          <Brain className="w-6 h-6 sm:w-7 sm:h-7 lg:w-8 lg:h-8 mr-2 sm:mr-3 text-primary-600" />
          <span className="truncate">AI Pattern Analysis</span>
        </h1>
        <button
          onClick={startAnalysis}
          className="btn-primary inline-flex items-center justify-center w-full sm:w-auto"
          disabled={loading}
        >
          {loading ? (
            <Clock className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <Brain className="w-4 h-4 mr-2" />
          )}
          <span className="truncate">{analysisData ? 'Re-analyze' : 'Start Analysis'}</span>
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className={`border rounded-md p-3 sm:p-4 ${
          error.includes('timeout') || error.includes('Failed to analyze') 
            ? 'bg-red-50 border-red-200' 
            : 'bg-yellow-50 border-yellow-200'
        }`}>
          <div className="flex">
            <AlertTriangle className={`h-4 w-4 sm:h-5 sm:w-5 flex-shrink-0 ${
              error.includes('timeout') || error.includes('Failed to analyze')
                ? 'text-red-400'
                : 'text-yellow-400'
            }`} />
            <div className="ml-2 sm:ml-3 min-w-0 flex-1">
              <h3 className={`text-xs sm:text-sm font-medium ${
                error.includes('timeout') || error.includes('Failed to analyze')
                  ? 'text-red-800'
                  : 'text-yellow-800'
              }`}>
                {error.includes('timeout') || error.includes('Failed to analyze') ? 'Error' : 'Notice'}
              </h3>
              <p className={`mt-1 text-xs sm:text-sm break-words ${
                error.includes('timeout') || error.includes('Failed to analyze')
                  ? 'text-red-700'
                  : 'text-yellow-700'
              }`}>
                {error}
              </p>
              {error.includes('timeout') && (
                <div className="mt-2 text-xs text-red-600">
                  <p><strong>Tips to resolve:</strong></p>
                  <ul className="list-disc list-inside mt-1 space-y-1">
                    <li>Try uploading a smaller dataset</li>
                    <li>Check your internet connection</li>
                    <li>Wait a few minutes and try again</li>
                    <li>Contact support if the issue persists</li>
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Analysis Results */}
      {analysisData ? (
        <>
          {renderExecutiveSummary()}
          {renderPatternSummary()}
          {renderTopThreats()}
          {renderDetailedAnalysis()}
        </>
      ) : (
        <div className="text-center py-8 sm:py-12">
          <Brain className="mx-auto h-10 w-10 sm:h-12 sm:w-12 text-gray-400" />
          <h3 className="mt-2 text-sm sm:text-base font-medium text-gray-900">No Analysis Available</h3>
          <p className="mt-1 text-xs sm:text-sm text-gray-500 px-4">
            Click "Start Analysis" to run LLM model
          </p>
        </div>
      )}
    </div>
  );
};

export default AIAnalysis;
