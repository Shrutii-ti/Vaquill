import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { casesAPI, documentsAPI, verdictsAPI, argumentsAPI } from '../services/api';

function CasePage() {
  const { caseId } = useParams();
  const navigate = useNavigate();

  // State
  const [caseData, setCaseData] = useState(null);
  const [documents, setDocuments] = useState({ sideA: [], sideB: [] });
  const [verdicts, setVerdicts] = useState([]);
  const [caseArguments, setCaseArguments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // Upload state
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadSide, setUploadSide] = useState('A');
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploading, setUploading] = useState(false);

  // Verdict generation state
  const [generatingVerdict, setGeneratingVerdict] = useState(false);

  // Argument submission state
  const [argumentText, setArgumentText] = useState({ A: '', B: '' });
  const [submittingArgument, setSubmittingArgument] = useState({ A: false, B: false });

  // Finalization state
  const [finalizing, setFinalizing] = useState(false);

  // Document deletion state
  const [deletingDocument, setDeletingDocument] = useState(null);

  // Load case data
  useEffect(() => {
    loadCaseData();
  }, [caseId]);

  const loadCaseData = async () => {
    try {
      setLoading(true);

      // Fetch all data in parallel
      const [caseInfo, docs, verdictsData, argsData] = await Promise.all([
        casesAPI.getById(caseId),
        documentsAPI.getAll(caseId),
        verdictsAPI.getAll(caseId),
        argumentsAPI.getAll(caseId),
      ]);

      setCaseData(caseInfo);

      // Separate documents by side
      setDocuments({
        sideA: docs.filter(doc => doc.side === 'A'),
        sideB: docs.filter(doc => doc.side === 'B'),
      });

      setVerdicts(verdictsData);
      setCaseArguments(argsData);
    } catch (err) {
      console.error('Error loading case:', err);
      setError('Failed to load case data');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    navigate('/dashboard');
  };

  const handleUploadClick = (side) => {
    setUploadSide(side);
    setShowUploadModal(true);
    setUploadFile(null);
    setUploadTitle('');
  };

  const handleUploadDocument = async (e) => {
    e.preventDefault();

    if (!uploadFile || !uploadTitle.trim()) {
      setError('Please provide both file and title');
      return;
    }

    setUploading(true);
    setError('');

    try {
      await documentsAPI.upload(caseId, uploadFile, uploadTitle, uploadSide);

      // Reload documents
      const docs = await documentsAPI.getAll(caseId);
      setDocuments({
        sideA: docs.filter(doc => doc.side === 'A'),
        sideB: docs.filter(doc => doc.side === 'B'),
      });

      // Close modal
      setShowUploadModal(false);
      setUploadFile(null);
      setUploadTitle('');
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.response?.data?.detail || 'Failed to upload document');
    } finally {
      setUploading(false);
    }
  };

  const handleGenerateVerdict = async () => {
    setGeneratingVerdict(true);
    setError('');

    try {
      const verdict = await verdictsAPI.generateInitial(caseId);

      // Reload all data to get updated case status and verdict
      await loadCaseData();
    } catch (err) {
      console.error('Verdict generation error:', err);
      setError(err.response?.data?.detail || 'Failed to generate verdict');
    } finally {
      setGeneratingVerdict(false);
    }
  };

  const handleSubmitArgument = async (side) => {
    if (!argumentText[side].trim()) {
      setError('Argument cannot be empty');
      setSuccessMessage('');
      return;
    }

    console.log(`[CasePage] Submitting argument for Side ${side}...`);
    setSubmittingArgument({ ...submittingArgument, [side]: true });
    setError('');
    setSuccessMessage('');

    try {
      const response = await argumentsAPI.submit(caseId, side, argumentText[side]);
      console.log(`[CasePage] Argument submitted successfully for Side ${side}`, response);

      // Clear argument text
      setArgumentText({ ...argumentText, [side]: '' });

      // Reload all data
      console.log('[CasePage] Reloading case data...');
      await loadCaseData();
      console.log('[CasePage] Case data reloaded successfully');

      // Show success message if waiting for other side
      if (response.waiting_for_other_side) {
        setSuccessMessage(`✓ Argument submitted! Waiting for Side ${side === 'A' ? 'B' : 'A'} to submit their argument...`);
      } else {
        setSuccessMessage(`✓ Argument submitted and new verdict generated!`);
      }
    } catch (err) {
      console.error('[CasePage] Argument submission error:', err);
      console.error('[CasePage] Error details:', {
        status: err.response?.status,
        statusText: err.response?.statusText,
        data: err.response?.data
      });
      setError(err.response?.data?.detail || 'Failed to submit argument');
    } finally {
      console.log(`[CasePage] Resetting submission state for Side ${side}`);
      setSubmittingArgument({ ...submittingArgument, [side]: false });
    }
  };

  const handleFinalizeCase = async () => {
    if (!window.confirm('Are you sure you want to finalize this case? This action cannot be undone and will lock the case permanently.')) {
      return;
    }

    setFinalizing(true);
    setError('');

    try {
      await casesAPI.finalize(caseId);

      // Reload case data
      await loadCaseData();

      alert('Case finalized successfully! The case is now locked and no further changes can be made.');
    } catch (err) {
      console.error('Finalization error:', err);
      setError(err.response?.data?.detail || 'Failed to finalize case');
    } finally {
      setFinalizing(false);
    }
  };

  const handleDeleteDocument = async (documentId) => {
    if (!window.confirm('Are you sure you want to delete this document?')) {
      return;
    }

    setDeletingDocument(documentId);
    setError('');

    try {
      await documentsAPI.delete(caseId, documentId);

      // Reload documents
      const docs = await documentsAPI.getAll(caseId);
      setDocuments({
        sideA: docs.filter(doc => doc.side === 'A'),
        sideB: docs.filter(doc => doc.side === 'B'),
      });
    } catch (err) {
      console.error('Delete document error:', err);
      setError(err.response?.data?.detail || 'Failed to delete document');
    } finally {
      setDeletingDocument(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-justice-blue mx-auto mb-4"></div>
          <p className="text-gray-600">Loading case...</p>
        </div>
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Error Loading Case</h2>
          <p className="text-gray-600 mb-6">Case not found</p>
          <button onClick={handleBack} className="btn-primary">
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const currentVerdict = verdicts.length > 0 ? verdicts[verdicts.length - 1] : null;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={handleBack}
                className="text-gray-600 hover:text-gray-900"
              >
                ← Back
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{caseData.title}</h1>
                <p className="text-sm text-gray-500">{caseData.case_number}</p>
              </div>
            </div>

            {/* Round Tracker & Finalize Button */}
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <div className="text-sm text-gray-500">Round Progress</div>
                <div className="text-lg font-bold text-justice-blue">
                  {caseData.current_round}/{caseData.max_rounds}
                </div>
              </div>
              <div className="px-3 py-1 rounded-full bg-blue-100 text-blue-700 text-sm font-medium">
                {caseData.status}
              </div>

              {/* Finalize Button - Show when max rounds reached and not finalized */}
              {caseData.status !== 'finalized' && caseData.current_round >= caseData.max_rounds && (
                <button
                  onClick={handleFinalizeCase}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 transition-colors disabled:opacity-50 text-sm"
                  disabled={finalizing}
                >
                  {finalizing ? 'Finalizing...' : '✓ Finalize Case'}
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Success Message Banner */}
      {successMessage && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-4">
          <div className="bg-green-50 border-l-4 border-green-500 p-4 rounded-lg">
            <div className="flex items-center justify-between">
              <p className="text-green-800 font-medium">{successMessage}</p>
              <button
                onClick={() => setSuccessMessage('')}
                className="text-green-600 hover:text-green-800 font-bold"
              >
                ✕
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Error Message Banner */}
      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-4">
          <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-lg">
            <div className="flex items-center justify-between">
              <p className="text-red-800 font-medium">{error}</p>
              <button
                onClick={() => setError('')}
                className="text-red-600 hover:text-red-800 font-bold"
              >
                ✕
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main 3-Column Layout */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* LEFT COLUMN - SIDE A */}
          <div className="space-y-6">
            <div className="card border-l-4 border-side-a-blue">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-side-a-blue">Side A - Plaintiff</h2>
                <span className="text-2xl">🔵</span>
              </div>

              {/* Documents Section */}
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">
                  Documents ({documents.sideA.length})
                </h3>
                {documents.sideA.length === 0 ? (
                  <div className="text-center py-4 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-500">No documents uploaded</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {documents.sideA.map(doc => (
                      <div
                        key={doc.id}
                        className="p-3 bg-blue-50 rounded-lg border border-blue-200 flex items-start justify-between"
                      >
                        <div className="flex-1">
                          <div className="font-medium text-sm text-gray-900">{doc.title}</div>
                          <div className="text-xs text-gray-500 mt-1">
                            {doc.file_name} • {doc.page_count} pages
                          </div>
                        </div>
                        {caseData.status !== 'finalized' && (
                          <button
                            onClick={() => handleDeleteDocument(doc.id)}
                            disabled={deletingDocument === doc.id}
                            className="ml-2 text-red-600 hover:text-red-800 text-xs font-medium disabled:opacity-50"
                            title="Delete document"
                          >
                            {deletingDocument === doc.id ? '...' : '🗑️'}
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Upload Button */}
              <button
                onClick={() => handleUploadClick('A')}
                className="w-full btn-secondary text-sm"
                disabled={caseData.status === 'finalized'}
              >
                + Upload Document
              </button>
            </div>

            {/* Arguments Section - Side A */}
            <div className="card border-l-4 border-side-a-blue">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Arguments</h3>

              <div className="space-y-3 mb-4 max-h-64 overflow-y-auto">
                {caseArguments
                  .filter(arg => arg.side === 'A')
                  .map(arg => (
                    <div key={arg.id} className="p-3 bg-blue-50 rounded-lg">
                      <div className="text-xs text-gray-500 mb-1">
                        Round {arg.round} • {new Date(arg.submitted_at).toLocaleDateString()}
                      </div>
                      <p className="text-sm text-gray-900">{arg.argument_text}</p>
                    </div>
                  ))}

                {caseArguments.filter(arg => arg.side === 'A').length === 0 && (
                  <p className="text-sm text-gray-500 text-center py-4">
                    No arguments submitted yet
                  </p>
                )}
              </div>

              {/* Submit Argument */}
              {caseData.status !== 'finalized' && caseData.current_round > 0 && (
                <div>
                  <textarea
                    value={argumentText.A}
                    onChange={(e) => setArgumentText({ ...argumentText, A: e.target.value })}
                    placeholder="Submit your argument..."
                    className="input-field resize-none mb-2"
                    rows="3"
                    disabled={submittingArgument.A}
                  />
                  <button
                    onClick={() => handleSubmitArgument('A')}
                    className="w-full btn-primary text-sm disabled:opacity-50"
                    disabled={submittingArgument.A || !argumentText.A.trim()}
                  >
                    {submittingArgument.A ? 'Submitting...' : 'Submit Argument'}
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* CENTER COLUMN - JUDGE / VERDICT */}
          <div className="space-y-6">
            <div className="card bg-gradient-to-br from-judge-gold to-yellow-600 text-white text-center py-8">
              <div className="text-6xl mb-4">⚖️</div>
              <h2 className="text-2xl font-bold mb-2">AI Judge</h2>
              <p className="text-yellow-100 text-sm">Mock Trial AI Verdict System</p>
            </div>

            {/* Max Rounds Reached Banner */}
            {caseData.status !== 'finalized' && caseData.current_round >= caseData.max_rounds && (
              <div className="bg-green-50 border-2 border-green-500 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="text-3xl">✓</div>
                    <div>
                      <h3 className="font-bold text-green-900">Maximum Rounds Completed</h3>
                      <p className="text-sm text-green-700">
                        All {caseData.max_rounds} argument rounds have been completed. You can now finalize the case to lock it permanently.
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={handleFinalizeCase}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 transition-colors disabled:opacity-50 whitespace-nowrap"
                    disabled={finalizing}
                  >
                    {finalizing ? 'Finalizing...' : 'Finalize Now'}
                  </button>
                </div>
              </div>
            )}

            {/* Verdict Display */}
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-gray-900">
                  {currentVerdict ? `Verdict - Round ${currentVerdict.round}` : 'No Verdict Yet'}
                </h3>
                {currentVerdict && (
                  <span className="text-sm text-gray-500">
                    {new Date(currentVerdict.created_at).toLocaleDateString()}
                  </span>
                )}
              </div>

              {currentVerdict ? (
                <div className="space-y-4">
                  {/* Summary */}
                  <div>
                    <h4 className="text-sm font-semibold text-gray-700 mb-2">Summary</h4>
                    <p className="text-gray-900">{currentVerdict.verdict_json.summary}</p>
                  </div>

                  {/* Winner */}
                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <span className="text-sm font-medium text-gray-700">Current Leader:</span>
                    <span className={`px-3 py-1 rounded-full text-sm font-bold ${
                      currentVerdict.verdict_json.winner === 'A'
                        ? 'bg-side-a-blue text-white'
                        : currentVerdict.verdict_json.winner === 'B'
                        ? 'bg-side-b-red text-white'
                        : 'bg-gray-300 text-gray-700'
                    }`}>
                      {currentVerdict.verdict_json.winner === 'A'
                        ? 'Side A'
                        : currentVerdict.verdict_json.winner === 'B'
                        ? 'Side B'
                        : 'Undecided'}
                    </span>
                  </div>

                  {/* Confidence Score */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700">Confidence</span>
                      <span className="text-sm font-bold text-gray-900">
                        {(currentVerdict.verdict_json.confidence_score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-judge-gold h-2 rounded-full transition-all"
                        style={{ width: `${currentVerdict.verdict_json.confidence_score * 100}%` }}
                      />
                    </div>
                  </div>

                  {/* Issues */}
                  {currentVerdict.verdict_json.issues && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-700 mb-2">Key Issues</h4>
                      <div className="space-y-2">
                        {currentVerdict.verdict_json.issues.map((issue, idx) => (
                          <div key={idx} className="p-3 bg-gray-50 rounded-lg">
                            <div className="font-medium text-sm text-gray-900 mb-1">
                              {issue.issue}
                            </div>
                            <div className="text-xs text-gray-600">
                              Finding: <span className="font-medium">{issue.finding}</span>
                            </div>
                            <p className="text-xs text-gray-600 mt-1">{issue.reasoning}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Final Decision */}
                  {currentVerdict.verdict_json.final_decision && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-700 mb-2">Final Decision</h4>
                      <p className="text-gray-900 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                        {currentVerdict.verdict_json.final_decision}
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="text-4xl mb-4">📋</div>
                  <p className="text-gray-600 mb-4">
                    No verdict generated yet. Upload documents for both sides to begin.
                  </p>
                  {documents.sideA.length > 0 && documents.sideB.length > 0 ? (
                    <button
                      onClick={handleGenerateVerdict}
                      className="btn-primary disabled:opacity-50"
                      disabled={generatingVerdict}
                    >
                      {generatingVerdict ? (
                        <span className="flex items-center justify-center">
                          <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          Generating Verdict...
                        </span>
                      ) : (
                        'Generate Initial Verdict'
                      )}
                    </button>
                  ) : (
                    <p className="text-sm text-gray-500">
                      {documents.sideA.length === 0 && 'Upload Side A documents • '}
                      {documents.sideB.length === 0 && 'Upload Side B documents'}
                    </p>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* RIGHT COLUMN - SIDE B */}
          <div className="space-y-6">
            <div className="card border-l-4 border-side-b-red">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-side-b-red">Side B - Defendant</h2>
                <span className="text-2xl">🔴</span>
              </div>

              {/* Documents Section */}
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">
                  Documents ({documents.sideB.length})
                </h3>
                {documents.sideB.length === 0 ? (
                  <div className="text-center py-4 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-500">No documents uploaded</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {documents.sideB.map(doc => (
                      <div
                        key={doc.id}
                        className="p-3 bg-red-50 rounded-lg border border-red-200 flex items-start justify-between"
                      >
                        <div className="flex-1">
                          <div className="font-medium text-sm text-gray-900">{doc.title}</div>
                          <div className="text-xs text-gray-500 mt-1">
                            {doc.file_name} • {doc.page_count} pages
                          </div>
                        </div>
                        {caseData.status !== 'finalized' && (
                          <button
                            onClick={() => handleDeleteDocument(doc.id)}
                            disabled={deletingDocument === doc.id}
                            className="ml-2 text-red-600 hover:text-red-800 text-xs font-medium disabled:opacity-50"
                            title="Delete document"
                          >
                            {deletingDocument === doc.id ? '...' : '🗑️'}
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Upload Button */}
              <button
                onClick={() => handleUploadClick('B')}
                className="w-full btn-secondary text-sm"
                disabled={caseData.status === 'finalized'}
              >
                + Upload Document
              </button>
            </div>

            {/* Arguments Section - Side B */}
            <div className="card border-l-4 border-side-b-red">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Arguments</h3>

              <div className="space-y-3 mb-4 max-h-64 overflow-y-auto">
                {caseArguments
                  .filter(arg => arg.side === 'B')
                  .map(arg => (
                    <div key={arg.id} className="p-3 bg-red-50 rounded-lg">
                      <div className="text-xs text-gray-500 mb-1">
                        Round {arg.round} • {new Date(arg.submitted_at).toLocaleDateString()}
                      </div>
                      <p className="text-sm text-gray-900">{arg.argument_text}</p>
                    </div>
                  ))}

                {caseArguments.filter(arg => arg.side === 'B').length === 0 && (
                  <p className="text-sm text-gray-500 text-center py-4">
                    No arguments submitted yet
                  </p>
                )}
              </div>

              {/* Submit Argument */}
              {caseData.status !== 'finalized' && caseData.current_round > 0 && (
                <div>
                  <textarea
                    value={argumentText.B}
                    onChange={(e) => setArgumentText({ ...argumentText, B: e.target.value })}
                    placeholder="Submit your argument..."
                    className="input-field resize-none mb-2"
                    rows="3"
                    disabled={submittingArgument.B}
                  />
                  <button
                    onClick={() => handleSubmitArgument('B')}
                    className="w-full btn-primary text-sm disabled:opacity-50"
                    disabled={submittingArgument.B || !argumentText.B.trim()}
                  >
                    {submittingArgument.B ? 'Submitting...' : 'Submit Argument'}
                  </button>
                </div>
              )}
            </div>
          </div>

        </div>
      </main>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">
                Upload Document - Side {uploadSide}
              </h2>
              <button
                onClick={() => setShowUploadModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <span className="text-2xl">×</span>
              </button>
            </div>

            <form onSubmit={handleUploadDocument} className="space-y-4">
              {/* Title */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Document Title <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={uploadTitle}
                  onChange={(e) => setUploadTitle(e.target.value)}
                  placeholder="e.g., Contract Agreement"
                  className="input-field"
                  required
                  disabled={uploading}
                />
              </div>

              {/* File */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  File <span className="text-red-500">*</span>
                </label>
                <input
                  type="file"
                  onChange={(e) => setUploadFile(e.target.files[0])}
                  accept=".pdf,.docx,.txt"
                  className="input-field"
                  required
                  disabled={uploading}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Supported: PDF, DOCX, TXT
                </p>
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
                  onClick={() => setShowUploadModal(false)}
                  className="flex-1 btn-secondary"
                  disabled={uploading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 btn-primary disabled:opacity-50"
                  disabled={uploading}
                >
                  {uploading ? 'Uploading...' : 'Upload'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default CasePage;
