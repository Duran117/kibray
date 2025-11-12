// Dynamic lists for steps, materials, tools, and file handling
function setupDynamicList(listId, inputId, hiddenField) {
  const list = document.getElementById(listId);
  const input = document.getElementById(inputId);
  const hidden = document.getElementById(hiddenField);
  let items = [];
  function render() {
    list.innerHTML = '';
    items.forEach((val, idx) => {
      const li = document.createElement('li');
      li.className = 'list-group-item d-flex align-items-center';
      // Checklist for steps only
      if (listId === 'steps-list') {
        const check = document.createElement('input');
        check.type = 'checkbox';
        check.className = 'form-check-input me-2';
        check.onclick = () => { check.checked = false; };
        li.appendChild(check);
      }
      li.appendChild(document.createTextNode(val));
      const del = document.createElement('button');
      del.type = 'button';
      del.className = 'btn btn-sm btn-danger ms-auto';
      del.innerHTML = '&times;';
      del.onclick = () => { items.splice(idx, 1); render(); };
      li.appendChild(del);
      list.appendChild(li);
    });
    hidden.value = JSON.stringify(items);
  }
  document.getElementById('add-' + listId.split('-')[0]).onclick = function() {
    const val = input.value.trim();
    if (val) { items.push(val); input.value = ''; render(); }
  };
  input.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      document.getElementById('add-' + listId.split('-')[0]).click();
    }
  });
  // Load initial data if present
  if (hidden.value) {
    try { items = JSON.parse(hidden.value); } catch {}
    render();
  }
}

document.addEventListener('DOMContentLoaded', function() {
  setupDynamicList('steps-list', 'step-input', 'id_steps');
  setupDynamicList('materials-list', 'material-input', 'id_materials_list');
  setupDynamicList('tools-list', 'tool-input', 'id_tools_list');

  // File uploads (reference photos/files) - simplified to show names
  const photoInput = document.getElementById('photo-input');
  const photoList = document.getElementById('photo-list');
  if (photoInput) {
    photoInput.addEventListener('change', function() {
      const files = Array.from(photoInput.files);
      photoList.innerHTML = '';
      if (files.length > 0) {
        const ul = document.createElement('ul');
        ul.className = 'list-group';
        files.forEach(file => {
          const li = document.createElement('li');
          li.className = 'list-group-item';
          li.textContent = file.name + ' (' + (file.size / 1024).toFixed(1) + ' KB)';
          ul.appendChild(li);
        });
        photoList.appendChild(ul);
      }
    });
  }
});
