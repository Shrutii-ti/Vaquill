import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI, casesAPI } from '../services/api';

function Dashboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');

  const [newCase, setNewCase] = useState({
    title: '',
    description: '',
    case_type: 'civil',
    jurisdiction: 'India',
  });

  // Load user and cases on mount
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const currentUser = authAPI.getCurrentUser();
      setUser(currentUser);

      const casesData = await casesAPI.getAll();
      setCases(casesData);
    } catch (err) {
      console.error('Error loading data:', err);
      setError('Failed to load cases');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    authAPI.logout();
    navigate('/login');
  };

  const handleCreateCase = async (e) => {
    e.preventDefault();
    setError('');

    if (!newCase.title.trim()) {
      setError('Case title is required');
      return;
    }

    setCreating(true);

    try {
      const createdCase = await casesAPI.create(newCase);

      // Add to list
      setCases([createdCase, ...cases]);

      // Close modal and reset form
      setShowCreateModal(false);
      setNewCase({
        title: '',
        description: '',
        case_type: 'civil',
        jurisdiction: 'India',
      });

      // Navigate to case page
      navigate(`/case/${createdCase.id}`);
    } catch (err) {
      console.error('Error creating case:', err);
      setError(err.response?.data?.detail || 'Failed to create case');
    } finally {
      setCreating(false);
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      draft: 'bg-gray-200 text-gray-700',
      ready: 'bg-blue-100 text-blue-700',
      in_progress: 'bg-yellow-100 text-yellow-700',
      finalized: 'bg-green-100 text-green-700',
    };

    const icons = {
      draft: '📝',
      ready: '⚡',
      in_progress: '⚖️',
      finalized: '✅',
    };

    return (
      <span className={`px-3 py-1 rounded-full text-sm font-medium ${badges[status] || badges.draft}`}>
        {icons[status]} {status.replace('_', ' ')}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-justice-blue mx-auto mb-4"></div>
          <p className="text-gray-600">Loading cases...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="text-3xl">🏛️</div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Mock Trial AI</h1>
                <p className="text-sm text-gray-500">
                  Welcome, {user?.full_name || 'User'}
                </p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="btn-secondary text-sm"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header with Create Button */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-3xl font-bold text-gray-900">My Cases</h2>
            <p className="text-gray-600 mt-1">
              {cases.length} {cases.length === 1 ? 'case' : 'cases'} total
            </p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary flex items-center space-x-2"
          >
            <span className="text-xl">+</span>
            <span>Create New Case</span>
          </button>
        </div>

        {/* Cases Grid */}
        {cases.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📋</div>
            <h3 className="text-xl font-semibold text-gray-700 mb-2">
              No cases yet
            </h3>
            <p className="text-gray-500 mb-6">
              Create your first case to get started with the AI Judge
            </p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="btn-primary"
            >
              Create Your First Case
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {cases.map((caseItem) => (
              <div
                key={caseItem.id}
                onClick={() => navigate(`/case/${caseItem.id}`)}
                className="card hover:shadow-lg transition-shadow cursor-pointer"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-1">
                      {caseItem.title}
                    </h3>
                    <p className="text-sm text-gray-500">
                      {caseItem.case_number}
                    </p>
                  </div>
                  {getStatusBadge(caseItem.status)}
                </div>

                <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                  {caseItem.description || 'No description provided'}
                </p>

                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center space-x-4">
                    <span className="text-gray-500">
                      <span className="font-medium">{caseItem.case_type}</span>
                    </span>
                    <span className="text-gray-400">•</span>
                    <span className="text-gray-500">{caseItem.jurisdiction}</span>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-gray-200 flex items-center justify-between text-xs text-gray-500">
                  <span>Round {caseItem.current_round}/{caseItem.max_rounds}</span>
                  <span>{new Date(caseItem.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Create Case Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Create New Case</h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <span className="text-2xl">×</span>
              </button>
            </div>

            <form onSubmit={handleCreateCase} className="space-y-4">
              {/* Title */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Case Title <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={newCase.title}
                  onChange={(e) => setNewCase({ ...newCase, title: e.target.value })}
                  placeholder="e.g., ABC vs XYZ Contract Dispute"
                  className="input-field"
                  required
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description (optional)
                </label>
                <textarea
                  value={newCase.description}
                  onChange={(e) => setNewCase({ ...newCase, description: e.target.value })}
                  placeholder="Brief case summary..."
                  rows="3"
                  className="input-field resize-none"
                />
              </div>

              {/* Case Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Case Type
                </label>
                <select
                  value={newCase.case_type}
                  onChange={(e) => setNewCase({ ...newCase, case_type: e.target.value })}
                  className="input-field"
                >
                  <option value="civil">Civil</option>
                  <option value="criminal">Criminal</option>
                  <option value="corporate">Corporate</option>
                  <option value="family">Family</option>
                  <option value="property">Property</option>
                  <option value="employment">Employment</option>
                  <option value="other">Other</option>
                </select>
              </div>

              {/* Jurisdiction */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Jurisdiction
                </label>
                <select
                  value={newCase.jurisdiction}
                  onChange={(e) => setNewCase({ ...newCase, jurisdiction: e.target.value })}
                  className="input-field"
                >
                  <option value="India">India</option>
                  <option value="USA">United States</option>
                  <option value="UK">United Kingdom</option>
                  <option value="Canada">Canada</option>
                  <option value="Australia">Australia</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              {/* Error Message */}
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                  <p className="text-sm">{error}</p>
                </div>
              )}

              {/* Buttons */}
              <div className="flex space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 btn-secondary"
                  disabled={creating}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 btn-primary disabled:opacity-50"
                  disabled={creating}
                >
                  {creating ? 'Creating...' : 'Create Case'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
