<template>
  <n-config-provider>
    <n-layout style="min-height: 100vh">
      <n-layout-content>
        <n-flex vertical align="center" justify="center" style="min-height: 100vh; gap: 16px">
          <n-icon size="64" color="#2080f0">
            <SettingsOutline />
          </n-icon>
          <n-h1 style="margin: 0">AI Assistant — Admin</n-h1>
          <n-text depth="3">Административный интерфейс — в разработке</n-text>
          <n-tag type="info" size="large">Admin Panel</n-tag>
        </n-flex>
      </n-layout-content>
    </n-layout>
  </n-config-provider>
</template>

<script setup lang="ts">
import { NConfigProvider, NLayout, NLayoutContent, NFlex, NIcon, NH1, NText, NTag } from 'naive-ui'
import { SettingsOutline } from '@vicons/ionicons5'
</script>
