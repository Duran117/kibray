import React, { useState, useEffect } from 'react';
import UserList from './UserList';
import InviteUser from './InviteUser';
import PermissionMatrix from './PermissionMatrix';
import api from '../../utils/api';
import { Users, UserPlus, Shield } from 'lucide-react';
import './UserManagement.css';

const UserManagement = () => {
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
      alert('Invite failed. Please try again.');
    }
  };

  const handleUpdateUser = async (userId, updates) => {
    try {
      await api.patch(`/users/${userId}/`, updates);
      fetchUsers();
    } catch (error) {
      console.error('Update failed:', error);
      alert('Update failed. Please try again.');
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!confirm('Are you sure you want to delete this user?')) return;
    
    try {
      await api.delete(`/users/${userId}/`);
      fetchUsers();
    } catch (error) {
      console.error('Delete failed:', error);
      alert('Delete failed. Please try again.');
    }
  };

  return (
    <div className="user-management">
      <div className="user-management-header">
        <div className="header-title">
          <Users size={28} />
          <h1>User Management</h1>
        </div>
        
        <div className="header-actions">
          <button onClick={() => setShowInviteModal(true)}>
            <UserPlus size={18} />
            Invite User
          </button>
          <button onClick={() => setShowPermissions(!showPermissions)}>
            <Shield size={18} />
            Permissions
          </button>
        </div>
      </div>

      {loading ? (
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading users...</p>
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
