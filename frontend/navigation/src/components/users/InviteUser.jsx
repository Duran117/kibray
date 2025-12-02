import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { X } from 'lucide-react';
import './InviteUser.css';

const InviteUser = ({ onInvite, onClose }) => {
  const { t } = useTranslation();
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
          <h2>{t('users.invite_new_user', { defaultValue: 'Invite New User' })}</h2>
          <button onClick={onClose}>
            <X size={20} />
          </button>
        </div>
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>{t('users.first_name', { defaultValue: 'First Name' })}</label>
            <input 
              type="text"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              required
            />
          </div>
          
          <div className="form-group">
            <label>{t('users.last_name', { defaultValue: 'Last Name' })}</label>
            <input 
              type="text"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              required
            />
          </div>
          
          <div className="form-group">
            <label>{t('auth.email')}</label>
            <input 
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          
          <div className="form-group">
            <label>{t('users.role', { defaultValue: 'Role' })}</label>
            <select value={role} onChange={(e) => setRole(e.target.value)}>
              <option value="pm">{t('users.roles.pm', { defaultValue: 'Project Manager' })}</option>
              <option value="admin">{t('users.roles.admin', { defaultValue: 'Administrator' })}</option>
              <option value="superintendent">{t('users.roles.superintendent', { defaultValue: 'Superintendent' })}</option>
              <option value="employee">{t('users.roles.employee', { defaultValue: 'Employee' })}</option>
              <option value="client">{t('users.roles.client', { defaultValue: 'Client' })}</option>
            </select>
          </div>
          
          <button type="submit">{t('users.invite')}</button>
        </form>
      </div>
    </div>
  );
};

export default InviteUser;
