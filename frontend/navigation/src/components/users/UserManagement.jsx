import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import UserList from './UserList';
import InviteUser from './InviteUser';
import PermissionMatrix from './PermissionMatrix';
import api from '../../utils/api';
import { Users, UserPlus, Shield } from 'lucide-react';
import './UserManagement.css';

const UserManagement = () => {
  const { t } = useTranslation();
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [showPermissions, setShowPermissions] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const data = await api.get('/users/');
      setUsers(data.results || data);
    } catch (error) {
      console.error('Failed to fetch users:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInviteUser = async (userData) => {
    try {
      await api.post('/users/invite/', userData);
      setShowInviteModal(false);
      fetchUsers();
    } catch (error) {
      console.error('Invite failed:', error);
      alert(t('errors.try_again'));
    }
  };

  const handleUpdateUser = async (userId, updates) => {
    try {
      await api.patch(`/users/${userId}/`, updates);
      fetchUsers();
    } catch (error) {
      console.error('Update failed:', error);
      alert(t('errors.try_again'));
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!confirm(t('users.remove_confirm'))) return;
    
    try {
      await api.delete(`/users/${userId}/`);
      fetchUsers();
    } catch (error) {
      console.error('Delete failed:', error);
      alert(t('errors.try_again'));
    }
  };

  return (
    <div className="user-management">
      <div className="user-management-header">
        <div className="header-title">
          <Users size={28} />
          <h1>{t('users.title')}</h1>
        </div>
        
        <div className="header-actions">
          <button onClick={() => setShowInviteModal(true)}>
            <UserPlus size={18} />
            {t('users.invite')}
          </button>
          <button onClick={() => setShowPermissions(!showPermissions)}>
            <Shield size={18} />
            {t('users.permissions')}
          </button>
        </div>
      </div>

      {loading ? (
        <div className="loading-container">
          <div className="spinner"></div>
          <p>{t('common.loading')}</p>
        </div>
      ) : (
        <>
          <UserList 
            users={users}
            onSelectUser={setSelectedUser}
            onUpdateUser={handleUpdateUser}
            onDeleteUser={handleDeleteUser}
          />
          
          {showPermissions && <PermissionMatrix users={users} />}
        </>
      )}

      {showInviteModal && (
        <InviteUser 
          onInvite={handleInviteUser}
          onClose={() => setShowInviteModal(false)}
        />
      )}
    </div>
  );
};

export default UserManagement;
