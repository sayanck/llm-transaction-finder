import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { TrendingUp, Users, DollarSign, Activity, AlertTriangle, RefreshCw, IndianRupee } from 'lucide-react';
import { SummaryStats, ApiResponse } from '../types';
import { apiService } from '../services/api';
import LoadingSpinner from './LoadingSpinner';

const Dashboard: React.FC = () => {
  const [summaryData, setSummaryData] = useState<SummaryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSummaryData();
  }, []);

  const fetchSummaryData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response: ApiResponse<SummaryStats> = await apiService.getSummary();
      setSummaryData(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch summary data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner text="Loading dashboard data..." />;
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <AlertTriangle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error Loading Dashboard</h3>
              <p className="mt-1 text-sm text-red-700">{error}</p>
              <button
                onClick={fetchSummaryData}
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

  if (!summaryData) {
    return <div className="p-8 text-center text-gray-500">No data available</div>;
  }

  // Prepare chart data
  const paymentStatusData = Object.entries(summaryData.payment_statuses).map(([status, count]) => ({
    name: status.replace('_', ' ').toUpperCase(),
    value: count
  }));

  const topUsersData = Object.entries(summaryData.top_users_by_transaction_count)
    .slice(0, 5)
    .map(([user, count]) => ({
      name: user.length > 20 ? user.substring(0, 20) + '...' : user,
      transactions: count
    }));

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

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
      day: 'numeric'
    });
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Transaction Dashboard</h1>
        <button
          onClick={fetchSummaryData}
          className="btn-secondary inline-flex items-center"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <div className="card-content">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <TrendingUp className="h-8 w-8 text-primary-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Transactions</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {summaryData.total_transactions.toLocaleString()}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-content">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Users className="h-8 w-8 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Unique Users</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {summaryData.unique_users.toLocaleString()}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-content">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <IndianRupee className="h-8 w-8 text-yellow-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Amount</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {formatCurrency(summaryData.total_amount)}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-content">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Activity className="h-8 w-8 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Average Amount</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {formatCurrency(summaryData.average_amount)}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Date Range */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">Data Range</h3>
        </div>
        <div className="card-content">
          <p className="text-sm text-gray-600">
            From <span className="font-semibold">{formatDate(summaryData.date_range.start)}</span> to{' '}
            <span className="font-semibold">{formatDate(summaryData.date_range.end)}</span>
          </p>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Payment Status Distribution */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium text-gray-900">Payment Status Distribution</h3>
          </div>
          <div className="card-content">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={paymentStatusData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }: any) => `${name} (${(percent * 100).toFixed(0)}%)`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {paymentStatusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Users by Transaction Count */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium text-gray-900">Top Users by Transaction Count</h3>
          </div>
          <div className="card-content">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={topUsersData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="transactions" fill="#3B82F6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Top Transaction Amounts */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">Most Common Transaction Amounts</h3>
        </div>
        <div className="card-content">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {Object.entries(summaryData.top_amounts).slice(0, 10).map(([amount, count]) => (
              <div key={amount} className="bg-gray-50 rounded-lg p-3 text-center">
                <p className="text-lg font-semibold text-gray-900">
                  {formatCurrency(parseFloat(amount))}
                </p>
                <p className="text-sm text-gray-600">{count} times</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
