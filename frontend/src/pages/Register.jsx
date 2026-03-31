import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

export default function Register() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      // Backend API-ku data anuppurom
      await axios.post('http://127.0.0.1:8000/auth/register', {
        name: name,
        email: email,
        password: password
      });
      alert("Registration Successful! Please login.");
      navigate('/login'); // Success aana udane login page-ku anuppudhu
    } catch (err) {
      setError(err.response?.data?.detail || "Registration failed. Try again.");
    }
  };

  return (
    <div style={{ padding: '50px', maxWidth: '400px', margin: 'auto' }}>
      <h2>Create an Account</h2>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      
      <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
        <input 
          type="text" placeholder="Full Name" required
          value={name} onChange={(e) => setName(e.target.value)} 
          style={{ padding: '10px' }}
        />
        <input 
          type="email" placeholder="Email Address" required
          value={email} onChange={(e) => setEmail(e.target.value)} 
          style={{ padding: '10px' }}
        />
        <input 
          type="password" placeholder="Password (min 6 chars)" required minLength="6"
          value={password} onChange={(e) => setPassword(e.target.value)} 
          style={{ padding: '10px' }}
        />
        <button type="submit" style={{ padding: '10px', background: 'blue', color: 'white', border: 'none', cursor: 'pointer' }}>
          Register
        </button>
      </form>
      <p>Already have an account? <a href="/login">Login here</a></p>
    </div>
  );
}