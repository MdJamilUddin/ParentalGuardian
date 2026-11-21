plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    namespace = "com.parentalguardian.child"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.parentalguardian.child"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "0.1.0"
    }

    buildTypes {
        debug {
            // 10.0.2.2 = your computer when running in the Android emulator
            buildConfigField("String", "BASE_URL", "\"http://10.0.2.2:8000\"")
        }
        release {
            // Replace with your real HTTPS server before releasing
            buildConfigField("String", "BASE_URL", "\"https://api.example.com\"")
            isMinifyEnabled = false
        }
        create("staging") {
            initWith(getByName("release"))
            // your staging server; installable for testing (debug-signed). Use a real key for production.
            buildConfigField("String", "BASE_URL", "\"https://staging.example.com/api\"")
            signingConfig = signingConfigs.getByName("debug")
            matchingFallbacks += "release"
        }
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}

dependencies {
    implementation(platform("androidx.compose:compose-bom:2024.09.00"))
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.activity:activity-compose:1.9.2")
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.work:work-runtime-ktx:2.9.1")
    implementation("com.google.android.gms:play-services-location:21.3.0")
    implementation("androidx.security:security-crypto:1.1.0-alpha06")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.8.1")
}
