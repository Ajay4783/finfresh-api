import { useState, useEffect } from 'react';
import axios from 'axios';

export default function Dashboard() {
  const [transactions, setTransactions] = useState([]);
  const [summary, setSummary] = useState(null);
  const [health, setHealth] = useState(null);
  const [formData, setFormData] = useState({ type: 'income', category: '', amount: '', date: '', description: '' });

  const token = localStorage.getItem('token');

  const fetchDashboardData = async () => {
    try {
      const config = { headers: { Authorization: `Bearer ${token}` } };
      
      // Moonu API-ayum thalaiva call panrom
      const transRes = await axios.get('http://127.0.0.1:8000/transactions', config);
      const summaryRes = await axios.get('http://127.0.0.1:8000/summary', config);
      const healthRes = await axios.get('http://127.0.0.1:8000/financial-health', config);

      setTransactions(transRes.data.data);
      setSummary(summaryRes.data);
      setHealth(healthRes.data);
    } catch (err) {
      console.error("Fetch failed", err);
    }
  };

  useEffect(() => { fetchDashboardData(); }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const config = { headers: { Authorization: `Bearer ${token}` } };
      await axios.post('http://127.0.0.1:8000/transactions', formData, config);
      setFormData({ type: 'income', category: '', amount: '', date: '', description: '' });
      fetchDashboardData(); 
    } catch (err) {
        alert("Error adding transaction");
    }
  };

  return (
    <div style={{ padding: '30px', fontFamily: 'sans-serif', maxWidth: '1000px', margin: 'auto' }}>
      <h1>FinFresh Dashboard</h1>
      
      {/* 1. Summary Cards (New Feature) */}
      {summary && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px', marginBottom: '30px' }}>
          <div style={{ background: '#e3f2fd', padding: '20px', borderRadius: '10px' }}>
            <p>Monthly Income</p>
            <h2>₹{summary.income}</h2>
          </div>
          <div style={{ background: '#ffebee', padding: '20px', borderRadius: '10px' }}>
            <p>Monthly Expenses</p>
            <h2>₹{summary.expense}</h2>
          </div>
          <div style={{ background: '#e8f5e9', padding: '20px', borderRadius: '10px' }}>
            <p>Savings Rate</p>
            <h2>{summary.savingsRate}%</h2>
          </div>
        </div>
      )}

      {/* 2. Professional Health Score Card */}
      {health && (
        <div style={{ background: '#343a40', color: 'white', padding: '20px', borderRadius: '10px', marginBottom: '30px' }}>
          <h2 style={{ margin: 0 }}>Financial Health: <span style={{ color: '#4caf50' }}>{health.score} / 100</span></h2>
          <p>Status: <strong>{health.category}</strong></p>
          <div style={{ background: '#495057', padding: '10px', borderRadius: '5px' }}>
            <p style={{ margin: '0 0 5px 0', fontSize: '14px' }}>Suggestions:</p>
            <ul style={{ margin: 0, paddingLeft: '20px' }}>
              {health.suggestions.map((s, i) => <li key={i}>{s}</li>)}
            </ul>
          </div>
        </div>
      )}

      {/* 3. Add Transaction Form */}
      <div style={{ background: '#f8f9fa', padding: '20px', borderRadius: '10px', marginBottom: '30px' }}>
        <h3>Add Transaction</h3>
        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <select value={formData.type} onChange={(e) => setFormData({...formData, type: e.target.value})} style={{padding: '10px'}}>
            <option value="income">Income</option>
            <option value="expense">Expense</option>
            <option value="investment">Investment</option>
            <option value="debt">Debt (EMIs)</option>
          </select>
          <input type="text" placeholder="Category" value={formData.category} onChange={(e) => setFormData({...formData, category: e.target.value})} style={{padding: '10px'}} required />
          <input type="number" placeholder="Amount" value={formData.amount} onChange={(e) => setFormData({...formData, amount: e.target.value})} style={{padding: '10px'}} required />
          <input type="date" value={formData.date} onChange={(e) => setFormData({...formData, date: e.target.value})} style={{padding: '10px'}} required />
          <button type="submit" style={{padding: '10px 20px', background: '#007bff', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer'}}>Add</button>
        </form>
      </div>

      {/* 4. Recent Transactions Table */}
      <h3>Recent Transactions</h3>
      <table border="0" cellPadding="15" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', boxShadow: '0 0 10px rgba(0,0,0,0.1)' }}>
        <thead>
          <tr style={{ background: '#f1f3f5' }}>
            <th>Date</th>
            <th>Type</th>
            <th>Category</th>
            <th>Amount</th>
          </tr>
        </thead>
        <tbody>
          {transactions.length > 0 ? (
            transactions.map(t => (
              <tr key={t.id} style={{ borderBottom: '1px solid #dee2e6' }}>
                <td>{t.date}</td>
                <td style={{ fontWeight: 'bold', color: t.type === 'income' ? '#28a745' : (t.type === 'expense' ? '#dc3545' : '#ffc107') }}>
                  {t.type.toUpperCase()}
                </td>
                <td>{t.category}</td>
                <td>₹{t.amount}</td>
              </tr>
            ))
          ) : (
            <tr><td colSpan="4" style={{ textAlign: 'center' }}>No transactions found for this month.</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}