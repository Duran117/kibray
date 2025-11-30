// Navigation Phase 3 API utilities (mock implementation)
// Replace endpoints with real Django REST API calls.

export async function fetchAssignedProjects(){
  // Simulate network latency
  await new Promise(r=>setTimeout(r,150));
  return [
    {id:1,name:'Central Plaza Renovation'},
    {id:2,name:'Coastal Highway Extension'},
    {id:3,name:'West Logistics Hub'}
  ];
}

export async function fetchProjectMetrics(projectId){
  await new Promise(r=>setTimeout(r,120));
  return {
    budgetUsed: projectId? Math.round(40+Math.random()*50)+'%':'--',
    schedulePerformance: projectId? (0.9+Math.random()*0.2).toFixed(2):'--',
    costPerformance: projectId? (0.95+Math.random()*0.15).toFixed(2):'--'
  };
}

export async function fetchAlerts(){
  await new Promise(r=>setTimeout(r,80));
  return [
    {id:'a1',title:'Safety inspection overdue',severity:'high',scope:'Site'},
    {id:'a2',title:'RFIs backlog increasing',severity:'medium',scope:'Docs'},
    {id:'a3',title:'Weather delay risk',severity:'low',scope:'Forecast'}
  ];
}

export async function fetchTasks(){
  await new Promise(r=>setTimeout(r,60));
  return [
    {id:'t1',title:'Update procurement log',status:'in_progress'},
    {id:'t2',title:'Approve subcontract invoices',status:'blocked'},
    {id:'t3',title:'Site walk QA/QC',status:'completed'}
  ];
}

export async function fetchChangeOrders(){
  await new Promise(r=>setTimeout(r,90));
  return [
    {id:'co1',title:'Scope add: Landscaping',amount:14500,status:'pending'},
    {id:'co2',title:'Value engineering savings',amount: -3500,status:'approved'},
    {id:'co3',title:'Material escalation',amount:7200,status:'rejected'}
  ];
}
