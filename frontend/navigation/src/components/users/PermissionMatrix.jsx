import React from 'react';
import { useTranslation } from 'react-i18next';
import './PermissionMatrix.css';

const PermissionMatrix = ({ users }) => {
  const { t } = useTranslation();
  const permissions = [
    { key: 'projects', label: t('users.permissions_sections.projects', { defaultValue: 'Projects' }) },
    { key: 'tasks', label: t('users.permissions_sections.tasks', { defaultValue: 'Tasks' }) },
    { key: 'change_orders', label: t('users.permissions_sections.change_orders', { defaultValue: 'Change Orders' }) },
    { key: 'files', label: t('users.permissions_sections.files', { defaultValue: 'Files' }) },
    { key: 'users', label: t('users.permissions_sections.users', { defaultValue: 'Users' }) },
    { key: 'analytics', label: t('users.permissions_sections.analytics', { defaultValue: 'Analytics' }) }
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
      <h3>{t('users.permission_matrix', { defaultValue: 'Permission Matrix' })}</h3>
      <div className="matrix-table-wrapper">
        <table>
          <thead>
            <tr>
              <th>{t('users.role', { defaultValue: 'Role' })}</th>
              {permissions.map(perm => (
                <th key={perm.key}>{perm.label}</th>
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
                    <span className="role-badge">{t(`users.roles.${role}`, { defaultValue: role })}</span>
                  </td>
                  {permissions.map(perm => (
                    <td key={perm.key}>
                      <div className="permission-checks">
                        <input 
                          type="checkbox" 
                          defaultChecked={perms.create}
                          title={t('common.create')}
                        />
                        <input 
                          type="checkbox" 
                          defaultChecked={perms.read}
                          title={t('common.read')}
                        />
                        <input 
                          type="checkbox" 
                          defaultChecked={perms.update}
                          title={t('common.update')}
                        />
                        <input 
                          type="checkbox" 
                          defaultChecked={perms.delete}
                          title={t('common.delete')}
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
