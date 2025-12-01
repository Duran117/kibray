import React from 'react';
import { Mail, Phone, Shield, Edit, Trash2 } from 'lucide-react';
import './UserList.css';

const UserList = ({ users, onSelectUser, onUpdateUser, onDeleteUser }) => {
  return (
    <div className="user-list">
      {users.map(user => (
        <div key={user.id} className="user-card">
          <div className="user-avatar">
            {user.username?.charAt(0).toUpperCase() || 'U'}
          </div>
          
          <div className="user-info">
            <h3>{user.first_name && user.last_name ? `${user.first_name} ${user.last_name}` : user.username}</h3>
            <p className="user-email">
              <Mail size={16} />
              {user.email}
            </p>
            {user.profile?.role && (
              <p className="user-role">
                <Shield size={16} />
                {user.profile.role}
              </p>
            )}
          </div>
          
          <div className="user-actions">
            <button 
              onClick={() => onSelectUser(user)}
              title="Edit user"
            >
              <Edit size={18} />
            </button>
            <button 
              onClick={() => onDeleteUser(user.id)}
              className="delete-btn"
              title="Delete user"
            >
              <Trash2 size={18} />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default UserList;
