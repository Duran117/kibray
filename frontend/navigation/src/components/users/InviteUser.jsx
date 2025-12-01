import React, { useState } from 'react';
import { X } from 'lucide-react';
import './InviteUser.css';

const InviteUser = ({ onInvite, onClose }) => {
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('pm');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onInvite({ 
      email, 
      role, 
      first_name: firstName, 
      last_name: lastName 
    });
    resetForm();
  };

  const resetForm = () => {
    setEmail('');
    setRole('pm');
    setFirstName('');
    setLastName('');
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Invite New User</h2>
          <button onClick={onClose}>
            <X size={20} />
          </button>
        </div>
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>First Name</label>
            <input 
              type="text"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              required
            />
          </div>
          
          <div className="form-group">
            <label>Last Name</label>
            <input 
              type="text"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              required
            />
          </div>
          
          <div className="form-group">
            <label>Email</label>
            <input 
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          
          <div className="form-group">
            <label>Role</label>
            <select value={role} onChange={(e) => setRole(e.target.value)}>
              <option value="pm">Project Manager</option>
              <option value="admin">Administrator</option>
              <option value="superintendent">Superintendent</option>
              <option value="employee">Employee</option>
              <option value="client">Client</option>
            </select>
          </div>
          
          <button type="submit">Invite User</button>
        </form>
      </div>
    </div>
  );
};

export default InviteUser;
