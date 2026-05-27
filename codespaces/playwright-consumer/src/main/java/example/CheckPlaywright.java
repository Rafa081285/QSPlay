package example;

import com.microsoft.playwright.Playwright;

public final class CheckPlaywright {
    private CheckPlaywright() {
    }

    public static void main(String[] args) {
        Package playwrightPackage = Playwright.class.getPackage();
        String version = playwrightPackage == null ? null : playwrightPackage.getImplementationVersion();
        System.out.println("Playwright class loaded from mirrored GitHub Packages artifacts.");
        System.out.println("Implementation version: " + (version == null ? "unknown" : version));
    }
}