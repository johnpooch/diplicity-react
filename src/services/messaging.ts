import { initializeApp } from 'firebase/app';
import { getMessaging, getToken, onMessage, Messaging } from 'firebase/messaging';

const appId = "diplicity-react/browser";

const firebaseConfig = {
    apiKey: "AIzaSyCsbBMuoeynbqGJ0WqKKd5hkXK4QyQtY-0",
    authDomain: "diplicity-engine.firebaseapp.com",
    databaseURL: "https://diplicity-engine.firebaseio.com",
    projectId: "diplicity-engine",
    storageBucket: "diplicity-engine.firebasestorage.app",
    messagingSenderId: "635122585664",
    appId: "1:635122585664:web:2a5a7f0a72c9647fa74fa5",
    measurementId: "G-SFEBT2PQ6W"
};

const app = initializeApp(firebaseConfig);
const messaging: Messaging = getMessaging(app);

export { messaging, getToken, onMessage, appId };