import React from 'react';
import './PermissionMatrix.css';

const PermissionMatrix = ({ users }) => {
  const permissions = [
    'Projects',
    'Tasks',
    'Change Orders',
    'Files',
    'Users',
    'Analytics'
  ];

  const getRolePermissions = (role) => {
    const roleMap = {
      admin: { create: true, read: true, update: true, delete: true },
      pm: { create: true, read: true, update: true, delete: false },
      superintendent: { create: true, read: true, update: true, delete: false },
      employee: { create: false, read: true, update: false, delete: false },
      client: { create: false, read: true, update: false, delete: false }
    };
    return roleMap[role] || roleMap.client;
  };

  return (
    <div className="permission-matrix">
      <h3>Permission Matrix</h3>
      <div className="matrix-table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Role</th>
              {permissions.map(perm => (
                <th key={perm}>{perm}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {users.map(user => {
              const role = user.profile?.role || 'client';
              const perms = getRolePermissions(role);
              
              return (
                <tr key={user.id}>
                  <td className="role-cell">
                    <strong>{user.username}</strong>
                    <span className="role-badge">{role}</span>
                  </td>
                  {permissions.map(perm => (
                    <td key={perm}>
                      <div className="permission-checks">
                        <input 
                          type="checkbox" 
                          defaultChecked={perms.create}
                          title="Create"
                        />
                        <input 
                          type="checkbox" 
                          defaultChecked={perms.read}
                          title="Read"
                        />
                        <input 
                          type="checkbox" 
                          defaultChecked={perms.update}
                          title="Update"
                        />
                        <input 
                          type="checkbox" 
                          defaultChecked={perms.delete}
                          title="Delete"
                        />
                      </div>
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default PermissionMatrix;
