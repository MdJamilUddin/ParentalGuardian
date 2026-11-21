package com.parentalguardian.child.sync

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import androidx.work.Constraints
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import java.util.concurrent.TimeUnit

class SyncWorker(ctx: Context, params: WorkerParameters) : CoroutineWorker(ctx, params) {
    override suspend fun doWork(): Result = try {
        Syncer.run(applicationContext)
        Result.success()
    } catch (e: Exception) {
        Result.retry()
    }
}

object SyncScheduler {
    private val online = Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build()

    fun schedule(ctx: Context) {
        val req = PeriodicWorkRequestBuilder<SyncWorker>(15, TimeUnit.MINUTES).setConstraints(online).build()
        WorkManager.getInstance(ctx).enqueueUniquePeriodicWork("guardian-sync", ExistingPeriodicWorkPolicy.KEEP, req)
    }

    fun syncNow(ctx: Context) {
        WorkManager.getInstance(ctx).enqueue(OneTimeWorkRequestBuilder<SyncWorker>().setConstraints(online).build())
    }
}
