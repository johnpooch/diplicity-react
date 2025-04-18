importScripts(
  "https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js"
);
importScripts(
  "https://www.gstatic.com/firebasejs/9.23.0/firebase-messaging-compat.js"
);
importScripts("https://cdnjs.cloudflare.com/ajax/libs/pako/1.0.6/pako.min.js");

// diplicity-react
// firebase.initializeApp({
//   apiKey: "AIzaSyDjCW9a1Y7wPTIQVyL_DMHmo61TzVFjx1c",
//   authDomain: "diplicity-react.firebaseapp.com",
//   projectId: "diplicity-react",
//   storageBucket: "diplicity-react.firebasestorage.app",
//   messagingSenderId: "919095022177",
//   appId: "1:919095022177:web:6303772970effd99759020",
// });

// diplicity-engine
firebase.initializeApp({
  apiKey: "AIzaSyCsbBMuoeynbqGJ0WqKKd5hkXK4QyQtY-0",
  authDomain: "diplicity-engine.firebaseapp.com",
  databaseURL: "https://diplicity-engine.firebaseio.com",
  projectId: "diplicity-engine",
  storageBucket: "diplicity-engine.firebasestorage.app",
  messagingSenderId: "635122585664",
  appId: "1:635122585664:web:2a5a7f0a72c9647fa74fa5",
  measurementId: "G-SFEBT2PQ6W",
});

const messaging = firebase.messaging();

const MessageNotification = {
  title: (message) =>
    `${message.Sender} -> ${message.ChannelMembers.join(", ")}`,
  body: (message) => message.Body,
  click_action: (message) =>
    `/Game/${message.GameID}/Channel/${message.ChannelMembers.join(
      ","
    )}/Messages`,
};

const PhaseNotification = {
  title: (gameDesc, phaseMeta) =>
    `${gameDesc}: ${phaseMeta.Season} ${phaseMeta.Year}, ${phaseMeta.Type}`,
  body: (gameDesc, phaseMeta) =>
    `${gameDesc}: ${phaseMeta.Season} ${phaseMeta.Year}, ${phaseMeta.Type} has changed state`,
  click_action: (gameID) => `/Game/${gameID}`,
};

messaging.onBackgroundMessage(async (payload) => {
  // Changed to async
  console.log("[firebase-messaging-sw.js] Received message", payload);

  // // const notificationTitle = "Test Notification!";
  // // const notificationOptions = {
  // //   body: "This is a test notification from the FCM console.",
  // //   icon: "/otto.png", // Ensure this path is correct!  Relative to the *root* of your project.
  // // };

  // const notificationTitle = payload.notification.title;
  // const notificationOptions = {
  //   body: payload.notification.body,
  //   icon: "/otto.png", // Ensure this path is correct!  Relative to the *root* of your project.
  // };

  try {
    await self.registration.showNotification(payload.title, {
      body: payload.body,
      icon: "/otto.png",
    });
  } catch (error) {
    console.error("Error showing notification:", error);
  }
});

// 	registration.showNotification(payload.notification.title, {
// 		requireInteraction: true,
// 		body: payload.notification.body,
// 		icon: "https://diplicity-engine.appspot.com/img/otto.png",
// 		tag: payload.notification.click_action,
// 		renotify: true,
// 		actions: [
// 			{
// 				action: payload.notification.click_action,
// 				title: "View"
// 			}
// 		]
// 	});

// function processNotification(payload, href) {
// 	payload.data = JSON.parse(
// 		pako.inflate(atob(payload.data.DiplicityJSON), { to: "string" })
// 	);
// 	const hrefURL = new URL(href);
// 	payload.notification = {};
// 	if (payload.data.type === "message") {
// 		payload.notification.click_action =
// 			hrefURL.protocol +
// 			"//" +
// 			hrefURL.host +
// 			"/Game/" +
// 			payload.data.message.GameID +
// 			"/Channel/" +
// 			payload.data.message.ChannelMembers.join(",") +
// 			"/Messages";
// 		payload.notification.title =
// 			payload.data.message.Sender +
// 			" -> " +
// 			payload.data.message.ChannelMembers.join(", ");
// 		payload.notification.body = payload.data.message.Body;
// 	} else if (payload.data.type === "phase") {
// 		payload.notification.click_action =
// 			hrefURL.protocol +
// 			"//" +
// 			hrefURL.host +
// 			"/Game/" +
// 			payload.data.gameID;
// 		payload.notification.title =
// 			payload.data.gameDesc +
// 			": " +
// 			payload.data.phaseMeta.Season +
// 			" " +
// 			payload.data.phaseMeta.Year +
// 			", " +
// 			payload.data.phaseMeta.Type;
// 		payload.notification.body =
// 			payload.data.gameDesc +
// 			": " +
// 			payload.data.phaseMeta.Season +
// 			" " +
// 			payload.data.phaseMeta.Year +
// 			", " +
// 			payload.data.phaseMeta.Type +
// 			" has changed state";
// 	}
// 	return payload;
// }

// const messaging = firebase.messaging();

// addEventListener("notificationclick", ev => {
// 	ev.waitUntil(
// 		clients.matchAll({
// 		  includeUncontrolled: true,
// 		  type: "window"
// 		}).then(foundClients => {
// 			if (foundClients.length > 0) {
// 				foundClients.forEach(client => {
// 					const message = {
// 						clickedNotification: {
// 							action: ev.notification.actions[0].action
// 						}
// 					};
// 					console.log("Sending", message, "to", client);
// 					client.postMessage(message);
// 					client.focus();
// 				});
// 			} else {
// 				console.log(
// 					"Found no client, opening new at",
// 					ev.notification.actions[0].action
// 				);
// 				clients.openWindow(ev.notification.actions[0].action);
// 			}
// 			ev.notification.close();
// 		})
// 	);
// });

// messaging.setBackgroundMessageHandler(payload => {
// 	payload = processNotification(payload, location.href);
// 	console.log("Message received in background: ", payload);
// 	registration.showNotification(payload.notification.title, {
// 		requireInteraction: true,
// 		body: payload.notification.body,
// 		icon: "https://diplicity-engine.appspot.com/img/otto.png",
// 		tag: payload.notification.click_action,
// 		renotify: true,
// 		actions: [
// 			{
// 				action: payload.notification.click_action,
// 				title: "View"
// 			}
// 		]
// 	});
// });

async function decompressZlibBase64(base64String) {
  // Decode the Base64 string into a Uint8Array
  const compressedData = Uint8Array.from(atob(base64String), (c) =>
    c.charCodeAt(0)
  );

  // Create a stream for decompression
  const decompressionStream = new DecompressionStream("deflate");
  const compressedStream = new Blob([compressedData]).stream();
  const decompressedStream = compressedStream.pipeThrough(decompressionStream);

  // Convert the decompressed stream back to a string
  const decompressedBlob = await new Response(decompressedStream).blob();
  return decompressedBlob.text();
}
