# Contractor Document Portal

A beginner-friendly HTML, CSS, and JavaScript web app for managing contractor contacts and job records for a contractor support business.

## Project Goal

This project is designed for a business that helps contractors with permitting, document organization, bookkeeping setup, business trackers, and other admin support.

The app is organized around two main record types:

1. **Contractors** — the main contact/business profile.
2. **Jobs** — separate project or service requests connected to a contractor.

This keeps the contractor in the system once, while allowing multiple jobs to be tracked separately by county, service type, document type, and status.

## File Structure

```text
contractor-document-portal/
├── index.html
├── styles.css
├── app.js
└── README.md
```

## Features

- Quick contractor intake form
- Required contractor fields:
  - Contact name
  - Business name
  - Email or phone
- Optional contractor/business fields:
  - License number
  - Business registration number
  - Business type
  - Mailing address
  - Notes
- Contractor dashboard/list
- Clickable contractor profiles
- Add jobs under a selected contractor
- Job table for each contractor
- Dashboard summary cards
- Firebase Firestore support
- Demo mode with sample data before Firebase config is added
- Responsive layout for smaller screens

## Job Fields

Each job belongs to one contractor and includes:

- Job name
- Project address
- County
- Service needed
- Document type
- Job notes
- Status

## Firebase Collections

This version uses two Firestore collections:

```text
contractors
```

Each contractor document stores the main business/contact profile.

```text
jobs
```

Each job document stores a `contractorId` field so the app knows which contractor the job belongs to.

Example job relationship:

```js
{
  contractorId: "abc123",
  jobName: "Gaston Permit Package",
  county: "Gaston",
  serviceNeeded: "Permit Assistance",
  status: "In Review"
}
```

## Firebase Setup

1. Go to [Firebase Console](https://console.firebase.google.com/).
2. Create a Firebase project.
3. Add a web app to the project.
4. Copy your `firebaseConfig` object.
5. Open `app.js`.
6. Paste your config into the clearly marked section:

## FIREBASE CONFIG 

apiKey: "AIzaSyD9WsbLlPfGbagpHOqVl5nTFdJ_C70cNrc",
authDomain: "construct-ops-40ded.firebaseapp.com",
projectId: "construct-ops-40ded",
storageBucket: "construct-ops-40ded.firebasestorage.app",
messagingSenderId: "54922290400",
appId: "1:54922290400:web:78e0d5e80aa2d23f07dc85",
measurementId: "G-HXZP8GKCSN"

## Firestore Setup

1. In Firebase Console, go to **Build > Firestore Database**.
2. Click **Create database**.
3. Start in test mode while learning.
4. Choose a location.
5. The app will use two collections:
   - `contractors`
   - `jobs`


## Next Steps

Future improvements could include:

- Contractor login page
- Admin login page
- File uploads with Firebase Storage
- Search and filter tools
- Edit contractor profile
- Edit job status
- Delete/archive records
- Email notifications
- Separate contractor and admin dashboards
