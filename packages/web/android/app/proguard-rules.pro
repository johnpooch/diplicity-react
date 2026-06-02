# Capacitor bridge
-keep class com.getcapacitor.** { *; }
-keep @com.getcapacitor.annotation.CapacitorPlugin class * { *; }

# Firebase / Google Services
-keep class com.google.firebase.** { *; }
-keep class com.google.android.gms.** { *; }

# Capacitor Firebase Messaging plugin
-keep class io.capawesome.capacitorjs.plugins.firebase.messaging.** { *; }

# Capacitor Social Login plugin
-keep class ee.forgr.capacitor.social.login.** { *; }

# Capacitor App plugin
-keep class com.capacitorjs.plugins.app.** { *; }

# Preserve JS interface annotations used by WebView
-keepattributes JavascriptInterface
-keepattributes *Annotation*

# Preserve stack traces for crash reporting
-keepattributes SourceFile,LineNumberTable
-renamesourcefileattribute SourceFile

# Firebase Kotlin extensions are unused — suppress the missing-class warning from R8
-dontwarn com.google.firebase.ktx.Firebase
