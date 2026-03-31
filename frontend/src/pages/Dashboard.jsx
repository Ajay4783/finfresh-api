import { useState, useEffect } from 'react';
import axios from 'axios';

export default function Dashboard() {
  const [transactions, setTransactions] = useState([]);
  const [health, setHealth] = useState(null);
  const [formData, setFormData] = useState({ type: 'income', category: '', amount: '', date: '', description: '' });

  const token = localStorage.getItem('token');

  const fetchDashboardData = async () => {
    try {
      const config = { headers: { Authorization: `Bearer ${token}` } };
      const transRes = await axios.get('http://127.0.0.1:8000/transactions', config);
      const healthRes = await axios.get('http://127.0.0.1:8000/health-score', config);
      setTransactions(transRes.data.data);
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
      fetchDashboardData(); // Update the list
    } catch (err) {
        alert("Error adding transaction");
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
      <h1>FinFresh Dashboard</h1>
      
      {/* Financial Health Score Card */}
      {health && (
        <div style={{ background: '#f0f4f8', padding: '15px', borderRadius: '10px', marginBottom: '20px' }}>
          <h3>Financial Health Score: <span style={{color: 'green'}}>{health.health_score} / 100</span></h3>
          <p>Status: <strong>{health.status}</strong></p>
          <p><em>Tip: {health.financial_tip}</em></p>
        </div>
      )}

      {/* Add Transaction Form */}
      <form onSubmit={handleSubmit} style={{ marginBottom: '30px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
        <select value={formData.type} onChange={(e) => setFormData({...formData, type: e.target.value})} style={{padding: '10px'}}>
          <option value="income">Income</option>
          <option value="expense">Expense</option>
        </select>
        <input type="text" placeholder="Category" value={formData.category} onChange={(e) => setFormData({...formData, category: e.target.value})} style={{padding: '10px'}} required />
        <input type="number" placeholder="Amount" value={formData.amount} onChange={(e) => setFormData({...formData, amount: e.target.value})} style={{padding: '10px'}} required />
        <input type="date" value={formData.date} onChange={(e) => setFormData({...formData, date: e.target.value})} style={{padding: '10px'}} required />
        <button type="submit" style={{padding: '10px', background: '#007bff', color: 'white', border: 'none'}}>Add Transaction</button>
      </form>

      {/* Recent Transactions List */}
      <h3>Recent Transactions</h3>
      <table border="1" cellPadding="10" style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ background: '#eee' }}>
            <th>Date</th>
            <th>Type</th>
            <th>Category</th>
            <th>Amount</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map(t => (
            <tr key={t.id}>
              <td>{t.date}</td>
              <td style={{ color: t.type === 'income' ? 'green' : 'red' }}>{t.type.toUpperCase()}</td>
              <td>{t.category}</td>
              <td>₹{t.amount}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}