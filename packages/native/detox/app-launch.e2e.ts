describe('App Launch', () => {
  beforeEach(async () => {
    await device.reloadReactNative();
  });

  it('should display welcome screen on launch', async () => {
    // Given the app launches
    await expect(element(by.text('Diplomacy Mobile'))).toBeVisible();
    await device.takeScreenshot('app-launched');

    // Then the welcome message is displayed
    await expect(
      element(by.text('Development environment ready!'))
    ).toBeVisible();
    await device.takeScreenshot('welcome-screen');
  });
});
