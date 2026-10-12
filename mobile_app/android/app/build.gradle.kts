import java.util.Properties

plugins {
    id("com.android.application")
    id("kotlin-android")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

// রিলিজ signing: android/key.properties থাকলে সেটা ব্যবহার হবে (ফাইলটা gitignored)
val keyProps = Properties()
val keyPropsFile = rootProject.file("key.properties")
val hasReleaseKey = keyPropsFile.exists()
if (hasReleaseKey) keyPropsFile.inputStream().use { keyProps.load(it) }

android {
    namespace = "com.futuretechai.chakriai"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }

    kotlinOptions {
        jvmTarget = JavaVersion.VERSION_11.toString()
    }

    defaultConfig {
        applicationId = "com.futuretechai.chakriai"
        // You can update the following values to match your application needs.
        // For more information, see: https://flutter.dev/to/review-gradle-config.
        minSdk = flutter.minSdkVersion
        // Play Store: নতুন অ্যাপ/আপডেটে API 36 (Android 16) লাগে (31 Aug 2026 থেকে)
        targetSdk = 36
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    signingConfigs {
        if (hasReleaseKey) {
            create("release") {
                keyAlias = keyProps.getProperty("keyAlias")
                keyPassword = keyProps.getProperty("keyPassword")
                storeFile = file(keyProps.getProperty("storeFile"))
                storePassword = keyProps.getProperty("storePassword")
            }
        }
    }

    buildTypes {
        release {
            // key.properties না থাকলে debug key দিয়ে sign হয় (শুধু যাচাইয়ের জন্য, Play Store-এ আপলোডযোগ্য নয়)
            signingConfig = if (hasReleaseKey) signingConfigs.getByName("release") else signingConfigs.getByName("debug")
        }
    }
}

flutter {
    source = "../.."
}
