// Contractor Document Portal + Firebase Firestore
// Contractors are saved separately from jobs.
// Each job stores contractorId so it can be linked back to the correct contractor.
// This file uses Firebase's web CDN, so you do not need npm yet.
// Run the project with Live Server or another local server.


import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.12.5/firebase-app.js';
import {
  getFirestore,
  collection,
  addDoc,
  onSnapshot,
  query,
  orderBy,
  serverTimestamp
} from 'https://www.gstatic.com/firebasejs/10.12.5/firebase-firestore.js';


// In Firebase Console:
// Project settings > General > Your apps > Web app > SDK setup and configuration
// Copy the firebaseConfig object and replace the placeholder values below.

const firebaseConfig = {
  apiKey: "AIzaSyD9WsbLlPfGbagpHOqVl5nTFdJ_C70cNrc",
  authDomain: "construct-ops-40ded.firebaseapp.com",
  projectId: "construct-ops-40ded",
  storageBucket: "construct-ops-40ded.firebasestorage.app",
  messagingSenderId: "54922290400",
  appId: "1:54922290400:web:78e0d5e80aa2d23f07dc85",
  measurementId: "G-HXZP8GKCSN"
};

// End Firebase Seetup 

const contractorForm = document.getElementById('contractorForm');
const jobForm = document.getElementById('jobForm');

const contractorList = document.getElementById('contractorList');
const contractorProfile = document.getElementById('contractorProfile');
const jobsTableBody = document.getElementById('jobsTableBody');

const contractorCount = document.getElementById('contractorCount');
const jobCount = document.getElementById('jobCount');
const openJobCount = document.getElementById('openJobCount');

const selectedContractorName = document.getElementById('selectedContractorName');
const selectedContractorMeta = document.getElementById('selectedContractorMeta');

const appMessage = document.getElementById('appMessage');
const contractorSubmitButton = document.getElementById('contractorSubmitButton');
const jobSubmitButton = document.getElementById('jobSubmitButton');

let contractors = [];
let jobs = [];
let selectedContractorId = null;
let db = null;

const sampleContractors = [
  {
    id: 'sample-1',
    contactName: 'Ariel Martinez',
    businessName: 'Martinez Electrical',
    email: 'ariel@example.com',
    phone: '704-555-0184',
    licenseNumber: 'NC-EL-12345',
    businessRegistrationNumber: '',
    businessType: 'Electrical',
    mailingAddress: 'Charlotte, NC',
    contractorNotes: 'Prefers text for quick updates.'
  },
  {
    id: 'sample-2',
    contactName: 'David Lopez',
    businessName: 'Lopez Flooring Co.',
    email: 'david@example.com',
    phone: '980-555-0138',
    licenseNumber: '',
    businessRegistrationNumber: 'BUS-78451',
    businessType: 'Other',
    mailingAddress: 'Gastonia, NC',
    contractorNotes: 'May need help keeping insurance and W-9 documents organized.'
  }
];

const sampleJobs = [
  {
    id: 'job-1',
    contractorId: 'sample-1',
    jobName: 'Azteca Electrical Permit Support',
    projectAddress: '1120 Central Ave, Charlotte, NC',
    county: 'Mecklenburg',
    serviceNeeded: 'Permit Assistance',
    documentType: 'Plans / Drawings',
    jobNotes: 'Needs electrical scope reviewed before permit submittal.',
    status: 'In Review'
  },
  {
    id: 'job-2',
    contractorId: 'sample-1',
    jobName: 'Catawba Fire Alarm Document Review',
    projectAddress: '300 Pine St, Newton, NC',
    county: 'Catawba',
    serviceNeeded: 'Document Review',
    documentType: 'Certificate of Insurance',
    jobNotes: 'Waiting on updated COI.',
    status: 'Waiting on Contractor'
  },
  {
    id: 'job-3',
    contractorId: 'sample-2',
    jobName: 'Gaston Invoice Tracker Setup',
    projectAddress: '45 Lakeview Dr, Gastonia, NC',
    county: 'Gaston',
    serviceNeeded: 'Business Tracker Setup',
    documentType: 'Invoice',
    jobNotes: 'Invoice tracker created for current project billing.',
    status: 'Submitted'
  }
];

function firebaseConfigIsReady() {
  return firebaseConfig.apiKey && !firebaseConfig.apiKey.includes('PASTE_YOUR');
}

// Display notification messages to the user
function showMessage(message, type = 'info') {
  appMessage.textContent = message;
  appMessage.className = `app-message ${type}`;
}

function getStatusClass(status) {
  return status.toLowerCase().replaceAll(' ', '-').replaceAll('/', '');
}

function contactMethodIsValid(email, phone) {
  return email.trim() !== '' || phone.trim() !== '';
}

function getSelectedContractor() {
  return contractors.find((contractor) => contractor.id === selectedContractorId);
}

function getJobsForSelectedContractor() {
  return jobs.filter((job) => job.contractorId === selectedContractorId);
}

// Update dashboard statistics
function renderStats() {
  const openStatuses = ['New', 'In Review', 'Waiting on Contractor', 'Missing Info', 'Submitted'];

  contractorCount.textContent = contractors.length;
  jobCount.textContent = jobs.length;
  openJobCount.textContent = jobs.filter((job) => openStatuses.includes(job.status)).length;
}

// Render contractor list in sidebar
function renderContractorList() {
  contractorList.innerHTML = '';

  if (contractors.length === 0) {
    contractorList.innerHTML = '<p class="empty-state">No contractors added yet. Add your first contractor with the form.</p>';
    return;
  }

  contractors.forEach((contractor) => {
    const contractorJobs = jobs.filter((job) => job.contractorId === contractor.id);
    const item = document.createElement('button');
    item.type = 'button';
    item.className = `contractor-item ${contractor.id === selectedContractorId ? 'active' : ''}`;

    item.innerHTML = `
      <span>
        <strong>${contractor.businessName}</strong>
        <small>${contractor.contactName} · ${contractor.email || contractor.phone}</small>
      </span>
      <span class="job-count">${contractorJobs.length} job${contractorJobs.length === 1 ? '' : 's'}</span>
    `;

    item.addEventListener('click', () => {
      selectedContractorId = contractor.id;
      renderApp();
    });

    contractorList.appendChild(item);
  });
}

function renderSelectedContractor() {
  const contractor = getSelectedContractor();
  const selectedJobs = getJobsForSelectedContractor();

  if (!contractor) {
    selectedContractorName.textContent = 'Select a contractor';
    selectedContractorMeta.textContent = 'After you select a contractor, their profile and jobs will show here.';
    contractorProfile.innerHTML = '';
    jobsTableBody.innerHTML = `
      <tr>
        <td colspan="5" class="empty-state">Select a contractor to view or add jobs.</td>
      </tr>
    `;
    jobForm.classList.add('disabled-form');
    jobSubmitButton.disabled = true;
    return;
  }

  jobForm.classList.remove('disabled-form');
  jobSubmitButton.disabled = false;

  selectedContractorName.textContent = contractor.businessName;
  selectedContractorMeta.textContent = `${contractor.contactName} · ${selectedJobs.length} job${selectedJobs.length === 1 ? '' : 's'} on file`;

  contractorProfile.innerHTML = `
    <div><strong>Contact</strong><span>${contractor.contactName}</span></div>
    <div><strong>Email</strong><span>${contractor.email || 'Not provided'}</span></div>
    <div><strong>Phone</strong><span>${contractor.phone || 'Not provided'}</span></div>
    <div><strong>Business Type</strong><span>${contractor.businessType || 'Not provided'}</span></div>
    <div><strong>License #</strong><span>${contractor.licenseNumber || 'Not provided'}</span></div>
    <div><strong>Business Reg. #</strong><span>${contractor.businessRegistrationNumber || 'Not provided'}</span></div>
    <div class="full-width"><strong>Mailing Address</strong><span>${contractor.mailingAddress || 'Not provided'}</span></div>
    <div class="full-width"><strong>Notes</strong><span>${contractor.contractorNotes || 'No notes yet.'}</span></div>
  `;

  renderJobsTable(selectedJobs);
}

function renderJobsTable(selectedJobs) {
  jobsTableBody.innerHTML = '';

  if (selectedJobs.length === 0) {
    jobsTableBody.innerHTML = `
      <tr>
        <td colspan="5" class="empty-state">No jobs added for this contractor yet.</td>
      </tr>
    `;
    return;
  }

  selectedJobs.forEach((job) => {
    const row = document.createElement('tr');

    row.innerHTML = `
      <td>
        <strong>${job.jobName}</strong><br>
        <small>${job.projectAddress}</small>
      </td>
      <td>${job.county}</td>
      <td>${job.serviceNeeded}</td>
      <td>${job.documentType || 'Not listed'}</td>
      <td><span class="status-pill status-${getStatusClass(job.status)}">${job.status}</span></td>
    `;

    jobsTableBody.appendChild(row);
  });
}

function renderApp() {
  renderStats();
  renderContractorList();
  renderSelectedContractor();
}

function getContractorFormData() {
  return {
    contactName: document.getElementById('contactName').value.trim(),
    businessName: document.getElementById('businessName').value.trim(),
    email: document.getElementById('email').value.trim(),
    phone: document.getElementById('phone').value.trim(),
    licenseNumber: document.getElementById('licenseNumber').value.trim(),
    businessRegistrationNumber: document.getElementById('businessRegistrationNumber').value.trim(),
    businessType: document.getElementById('businessType').value,
    mailingAddress: document.getElementById('mailingAddress').value.trim(),
    contractorNotes: document.getElementById('contractorNotes').value.trim(),
    createdAt: serverTimestamp()
  };
}

function getJobFormData() {
  return {
    contractorId: selectedContractorId,
    jobName: document.getElementById('jobName').value.trim(),
    projectAddress: document.getElementById('projectAddress').value.trim(),
    county: document.getElementById('county').value,
    serviceNeeded: document.getElementById('serviceNeeded').value,
    documentType: document.getElementById('documentType').value,
    jobNotes: document.getElementById('jobNotes').value.trim(),
    status: document.getElementById('status').value,
    createdAt: serverTimestamp()
  };
}

function listenForContractors() {
  const contractorsCollection = collection(db, 'contractors');
  const contractorsQuery = query(contractorsCollection, orderBy('createdAt', 'desc'));

  onSnapshot(
    contractorsQuery,
    (snapshot) => {
      contractors = snapshot.docs.map((doc) => ({
        id: doc.id,
        ...doc.data()
      }));

      if (selectedContractorId && !contractors.some((contractor) => contractor.id === selectedContractorId)) {
        selectedContractorId = null;
      }

      renderApp();
      showMessage('Connected to Firebase. Contractors are loading from Firestore.', 'success');
    },
    (error) => {
      console.error('Error loading contractors:', error);
      showMessage('Firebase connected, but contractors could not load. Check Firestore rules and console errors.', 'error');
    }
  );
}

function listenForJobs() {
  const jobsCollection = collection(db, 'jobs');
  const jobsQuery = query(jobsCollection, orderBy('createdAt', 'desc'));

  onSnapshot(
    jobsQuery,
    (snapshot) => {
      jobs = snapshot.docs.map((doc) => ({
        id: doc.id,
        ...doc.data()
      }));

      renderApp();
    },
    (error) => {
      console.error('Error loading jobs:', error);
      showMessage('Firebase connected, but jobs could not load. Check Firestore rules and console errors.', 'error');
    }
  );
}

async function saveContractor(contractor) {
  if (!db) {
    const localContractor = {
      ...contractor,
      id: crypto.randomUUID(),
      createdAt: new Date()
    };

    contractors.unshift(localContractor);
    selectedContractorId = localContractor.id;
    return;
  }

  const contractorsCollection = collection(db, 'contractors');
  const docRef = await addDoc(contractorsCollection, contractor);
  selectedContractorId = docRef.id;
}

async function saveJob(job) {
  if (!db) {
    jobs.unshift({
      ...job,
      id: crypto.randomUUID(),
      createdAt: new Date()
    });
    return;
  }

  const jobsCollection = collection(db, 'jobs');
  await addDoc(jobsCollection, job);
}

contractorForm.addEventListener('submit', async (event) => {
  event.preventDefault();

  const newContractor = getContractorFormData();

  if (!contactMethodIsValid(newContractor.email, newContractor.phone)) {
    showMessage('Please enter at least one contact method: email or phone.', 'error');
    return;
  }

  contractorSubmitButton.disabled = true;
  contractorSubmitButton.textContent = 'Saving...';

  try {
    await saveContractor(newContractor);
    contractorForm.reset();
    renderApp();
    showMessage(db ? 'Contractor saved to Firestore.' : 'Contractor added in demo mode. Add Firebase config to save permanently.', 'success');
  } catch (error) {
    console.error('Error saving contractor:', error);
    showMessage('Contractor was not saved. Check your Firebase config, Firestore rules, and browser console.', 'error');
  } finally {
    contractorSubmitButton.disabled = false;
    contractorSubmitButton.textContent = 'Save Contractor';
  }
});

jobForm.addEventListener('submit', async (event) => {
  event.preventDefault();

  if (!selectedContractorId) {
    showMessage('Select a contractor before adding a job.', 'error');
    return;
  }

  jobSubmitButton.disabled = true;
  jobSubmitButton.textContent = 'Saving...';

  try {
    const newJob = getJobFormData();
    await saveJob(newJob);
    jobForm.reset();
    renderApp();
    showMessage(db ? 'Job saved to Firestore.' : 'Job added in demo mode. Add Firebase config to save permanently.', 'success');
  } catch (error) {
    console.error('Error saving job:', error);
    showMessage('Job was not saved. Check your Firebase config, Firestore rules, and browser console.', 'error');
  } finally {
    jobSubmitButton.disabled = false;
    jobSubmitButton.textContent = 'Save Job';
  }
});

function startApp() {
  if (!firebaseConfigIsReady()) {
    contractors = sampleContractors;
    jobs = sampleJobs;
    selectedContractorId = contractors[0]?.id || null;
    renderApp();
    showMessage('Firebase config placeholder detected. You can test the layout in demo mode, but records will not save permanently.', 'warning');
    return;
  }

  const app = initializeApp(firebaseConfig);
  db = getFirestore(app);
  listenForContractors();
  listenForJobs();
}

startApp();
