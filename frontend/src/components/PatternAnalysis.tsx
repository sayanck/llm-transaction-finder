import React, { useState, useEffect } from 'react';
import { AlertTriangle, RefreshCw, Users, Clock, DollarSign, IndianRupee } from 'lucide-react';
import { PatternData, ApiResponse } from '../types';
import { apiService } from '../services/api';
import LoadingSpinner from './LoadingSpinner';
import RiskBadge from './RiskBadge';

const PatternAnalysis: React.FC = () => {
  const [patternData, setPatternData] = useState<PatternData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPattern, setSelectedPattern] = useState<string>('frequent_pairs');

  useEffect(() => {
    fetchPatternData();
  }, []);

  const fetchPatternData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response: ApiResponse<PatternData> = await apiService.getPatterns();
      setPatternData(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch pattern data');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'INR'
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const patternTabs = [
    { key: 'frequent_pairs', label: 'Frequent Pairs', icon: Users },
    { key: 'round_amounts', label: 'Round Amounts', icon: IndianRupee },
    { key: 'high_activity_periods', label: 'High Activity', icon: Clock },
    { key: 'repeated_amounts', label: 'Repeated Amounts', icon: RefreshCw },
    { key: 'quick_successive', label: 'Quick Transactions', icon: AlertTriangle },
  ];

  if (loading) {
    return <LoadingSpinner text="Analyzing transaction patterns..." />;
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <AlertTriangle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error Loading Patterns</h3>
              <p className="mt-1 text-sm text-red-700">{error}</p>
              <button
                onClick={fetchPatternData}
                className="mt-3 btn-primary inline-flex items-center"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Retry
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!patternData) {
    return <div className="p-8 text-center text-gray-500">No pattern data available</div>;
  }

  const renderFrequentPairs = () => (
    <div className="space-y-4">
      <div className="text-sm text-gray-600 mb-4">
        Identified {patternData.frequent_pairs.length} frequent user pairs (3+ transactions between same users)
      </div>
      {patternData.frequent_pairs.map((pair, index) => (
        <div key={index} className="card">
          <div className="card-content">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h4 className="font-semibold text-gray-900">
                  {pair.sender_name} → {pair.receiver_name}
                </h4>
                <p className="text-sm text-gray-600">
                  {pair.transaction_count} transactions • {formatCurrency(pair.total_amount)} total
                </p>
              </div>
              <RiskBadge 
                level={pair.transaction_count >= 8 ? 'high' : pair.transaction_count >= 5 ? 'medium' : 'low'} 
              />
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div>
                <p className="text-xs text-gray-500">Average Amount</p>
                <p className="font-semibold">{formatCurrency(pair.average_amount)}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Amount Std Dev</p>
                <p className="font-semibold">{formatCurrency(pair.amount_std)}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">First Transaction</p>
                <p className="text-sm">{formatDate(pair.first_transaction)}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Last Transaction</p>
                <p className="text-sm">{formatDate(pair.last_transaction)}</p>
              </div>
            </div>

            <details className="mt-4">
              <summary className="cursor-pointer text-sm font-medium text-primary-600 hover:text-primary-700">
                View Sample Transactions
              </summary>
              <div className="mt-2 space-y-2">
                {pair.sample_transactions.map((tx, txIndex) => (
                  <div key={txIndex} className="bg-gray-50 rounded p-2 text-sm">
                    <div className="flex justify-between">
                      <span>ID: {tx.transaction_id}</span>
                      <span className="font-semibold">{formatCurrency(tx.amount)}</span>
                    </div>
                    <div className="text-gray-600">
                      {formatDate(tx.created_at)} • {tx.remarks}
                    </div>
                  </div>
                ))}
              </div>
            </details>
          </div>
        </div>
      ))}
    </div>
  );

  const renderRoundAmounts = () => (
    <div className="space-y-4">
      <div className="text-sm text-gray-600 mb-4">
        Found {patternData.round_amounts.length} transactions with round amounts (potentially suspicious)
      </div>
      <div className="grid gap-4">
        {patternData.round_amounts.map((tx, index) => (
          <div key={index} className="card">
            <div className="card-content">
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-semibold text-gray-900">
                    {tx.user_name} → {tx.reciever_name}
                  </h4>
                  <p className="text-sm text-gray-600">
                    Transaction ID: {tx.transaction_id}
                  </p>
                  <p className="text-sm text-gray-600 mt-1">
                    {formatDate(tx.created_at)}
                  </p>
                  {tx.remarks && (
                    <p className="text-sm text-gray-500 mt-1 italic">"{tx.remarks}"</p>
                  )}
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-gray-900">
                    {formatCurrency(tx.amount)}
                  </p>
                  <RiskBadge level="medium" size="sm" />
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderHighActivityPeriods = () => (
    <div className="space-y-4">
      <div className="text-sm text-gray-600 mb-4">
        Identified {patternData.high_activity_periods.length} high-activity time periods
      </div>
      {patternData.high_activity_periods.map((period, index) => (
        <div key={index} className="card">
          <div className="card-content">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h4 className="font-semibold text-gray-900">
                  {formatDate(period.time_period)}
                </h4>
                <p className="text-sm text-gray-600">
                  {period.transaction_count} transactions in one hour
                </p>
              </div>
              <RiskBadge 
                level={period.transaction_count >= 20 ? 'high' : period.transaction_count >= 10 ? 'medium' : 'low'} 
              />
            </div>
            
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div>
                <p className="text-xs text-gray-500">Unique Users</p>
                <p className="font-semibold">{period.unique_users}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Total Amount</p>
                <p className="font-semibold">{formatCurrency(period.total_amount)}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Avg per Transaction</p>
                <p className="font-semibold">
                  {formatCurrency(period.total_amount / period.transaction_count)}
                </p>
              </div>
            </div>

            <details className="mt-4">
              <summary className="cursor-pointer text-sm font-medium text-primary-600 hover:text-primary-700">
                View Sample Transactions
              </summary>
              <div className="mt-2 space-y-2">
                {period.sample_transactions.map((tx, txIndex) => (
                  <div key={txIndex} className="bg-gray-50 rounded p-2 text-sm">
                    <div className="flex justify-between">
                      <span>{tx.user_name}</span>
                      <span className="font-semibold">{formatCurrency(tx.amount)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </details>
          </div>
        </div>
      ))}
    </div>
  );

  const renderRepeatedAmounts = () => (
    <div className="space-y-4">
      <div className="text-sm text-gray-600 mb-4">
        Found {patternData.repeated_amounts.length} amounts that appear multiple times
      </div>
      {patternData.repeated_amounts.map((amount, index) => (
        <div key={index} className="card">
          <div className="card-content">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h4 className="font-semibold text-gray-900">
                  {formatCurrency(amount.amount)}
                </h4>
                <p className="text-sm text-gray-600">
                  Appears {amount.frequency} times
                </p>
              </div>
              <RiskBadge 
                level={amount.frequency >= 10 ? 'high' : amount.frequency >= 5 ? 'medium' : 'low'} 
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <p className="text-xs text-gray-500">Unique Senders</p>
                <p className="font-semibold">{amount.unique_senders}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Unique Receivers</p>
                <p className="font-semibold">{amount.unique_receivers}</p>
              </div>
            </div>

            <details className="mt-4">
              <summary className="cursor-pointer text-sm font-medium text-primary-600 hover:text-primary-700">
                View Sample Transactions
              </summary>
              <div className="mt-2 space-y-2">
                {amount.sample_transactions.map((tx, txIndex) => (
                  <div key={txIndex} className="bg-gray-50 rounded p-2 text-sm">
                    <div className="flex justify-between">
                      <span>{tx.user_name} → {tx.reciever_name}</span>
                      <span className="text-gray-600">{formatDate(tx.created_at)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </details>
          </div>
        </div>
      ))}
    </div>
  );

  const renderQuickSuccessive = () => (
    <div className="space-y-4">
      <div className="text-sm text-gray-600 mb-4">
        Found {patternData.quick_successive.length} quick successive transactions (within 5 minutes)
      </div>
      {patternData.quick_successive.map((tx, index) => (
        <div key={index} className="card">
          <div className="card-content">
            <div className="flex justify-between items-start">
              <div>
                <h4 className="font-semibold text-gray-900">
                  {tx.user_name} → {tx.reciever_name}
                </h4>
                <p className="text-sm text-gray-600">
                  Transaction ID: {tx.transaction_id}
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  {formatDate(tx.created_at)}
                </p>
                <p className="text-sm text-orange-600 font-medium">
                  {Math.round(tx.time_diff)} seconds after previous transaction
                </p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(tx.amount)}
                </p>
                <RiskBadge 
                  level={tx.time_diff < 60 ? 'high' : tx.time_diff < 180 ? 'medium' : 'low'} 
                  size="sm" 
                />
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );

  const renderPatternContent = () => {
    switch (selectedPattern) {
      case 'frequent_pairs':
        return renderFrequentPairs();
      case 'round_amounts':
        return renderRoundAmounts();
      case 'high_activity_periods':
        return renderHighActivityPeriods();
      case 'repeated_amounts':
        return renderRepeatedAmounts();
      case 'quick_successive':
        return renderQuickSuccessive();
      default:
        return <div>Pattern not found</div>;
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Pattern Analysis</h1>
        <button
          onClick={fetchPatternData}
          className="btn-secondary inline-flex items-center"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </button>
      </div>

      {/* Pattern Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {patternTabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = selectedPattern === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => setSelectedPattern(tab.key)}
                className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                  isActive
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="w-4 h-4 mr-2" />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Pattern Content */}
      <div>
        {renderPatternContent()}
      </div>
    </div>
  );
};

export default PatternAnalysis;
