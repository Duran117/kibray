import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../utils/api';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  // Redirect if already authenticated (support test and production tokens)
  useEffect(() => {
    const isAuth = !!localStorage.getItem('authToken') || !!localStorage.getItem('kibray_access_token');
    if (isAuth) {
      navigate('/dashboard', { replace: true });
    }
  }, [navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const data = await api.post('/auth/login/', { username, password });
      localStorage.setItem('authToken', data.token || data.access);
      navigate('/dashboard');
    } catch (err) {
      console.error('Login failed:', err);
      setError('Invalid credentials. Please try again.');
    }
  };

  return (
    <div data-testid="login-page" className="login-page">
      <div className="login-container">
        <div className="login-header">
          <h1 className="login-title">Kibray Construction Management</h1>
          <p className="login-subtitle">Sign in to continue</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          {error && (
            <div className="error-message">
              <span>{error}</span>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="username">Email or Username</label>
            <div className="input-wrapper">
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <div className="input-wrapper">
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
              />
            </div>
          </div>

          <button type="submit" className="login-btn">
            <span>Sign In</span>
          </button>
        </form>

        <div className="login-footer">
          <p>New to Kibray? Contact your administrator for access.</p>
        </div>
      </div>
    </div>
  );
};

export default Login;
