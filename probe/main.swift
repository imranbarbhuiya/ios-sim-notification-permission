import UIKit
import UserNotifications

/// Reads the app's notification authorization, asks for it, and shows both.
/// A system prompt left on screen means the status was not set beforehand.
@main
final class AppDelegate: UIResponder, UIApplicationDelegate {
  func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
    true
  }

  func application(_ application: UIApplication, configurationForConnecting session: UISceneSession, options: UIScene.ConnectionOptions) -> UISceneConfiguration {
    let configuration = UISceneConfiguration(name: nil, sessionRole: session.role)
    configuration.delegateClass = SceneDelegate.self
    return configuration
  }
}

final class SceneDelegate: UIResponder, UIWindowSceneDelegate {
  var window: UIWindow?

  func scene(_ scene: UIScene, willConnectTo session: UISceneSession, options: UIScene.ConnectionOptions) {
    guard let windowScene = scene as? UIWindowScene else { return }
    let window = UIWindow(windowScene: windowScene)
    let controller = UIViewController()
    controller.view.backgroundColor = .white
    let label = UILabel(frame: controller.view.bounds.insetBy(dx: 24, dy: 160))
    label.numberOfLines = 0
    label.font = .monospacedSystemFont(ofSize: 18, weight: .regular)
    label.text = "asking..."
    label.accessibilityIdentifier = "status"
    controller.view.addSubview(label)
    window.rootViewController = controller
    window.makeKeyAndVisible()
    self.window = window

    let center = UNUserNotificationCenter.current()
    center.getNotificationSettings { before in
      center.requestAuthorization(options: [.alert, .sound, .badge]) { granted, _ in
        center.getNotificationSettings { after in
          let text = "before=\(Self.name(before.authorizationStatus)) granted=\(granted) after=\(Self.name(after.authorizationStatus))"
          DispatchQueue.main.async { label.text = text }
        }
      }
    }
  }

  private static func name(_ status: UNAuthorizationStatus) -> String {
    switch status {
    case .notDetermined: return "notDetermined"
    case .denied: return "denied"
    case .authorized: return "authorized"
    case .provisional: return "provisional"
    case .ephemeral: return "ephemeral"
    @unknown default: return "unknown(\(status.rawValue))"
    }
  }
}
