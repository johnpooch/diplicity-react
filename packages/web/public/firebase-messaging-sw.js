importScripts(
  "https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js"
);
importScripts(
  "https://www.gstatic.com/firebasejs/9.23.0/firebase-messaging-compat.js"
);
importScripts("https://cdnjs.cloudflare.com/ajax/libs/pako/1.0.6/pako.min.js");

// diplicity-react
firebase.initializeApp({
  apiKey: "AIzaSyDjCW9a1Y7wPTIQVyL_DMHmo61TzVFjx1c",
  authDomain: "diplicity-react.firebaseapp.com",
  projectId: "diplicity-react",
  storageBucket: "diplicity-react.firebasestorage.app",
  messagingSenderId: "919095022177",
  appId: "1:919095022177:web:6303772970effd99759020",
});

const messaging = firebase.messaging();
