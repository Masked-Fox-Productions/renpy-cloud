# Example Ren'Py game with renpy-cloud integration
# This demonstrates how to integrate cloud save sync into a Ren'Py game

# Game configuration
define e = Character("Eileen", color="#c8ffc8")

# Initialize renpy-cloud
init python:
    import renpy_cloud
    
    # Configure the cloud sync client
    # Replace these values with your actual AWS deployment outputs
    renpy_cloud.configure(
        api_base_url="https://your-api-id.execute-api.us-east-1.amazonaws.com",
        game_id="example_renpy_game",
        aws_region="us-east-1",
        cognito_user_pool_id="us-east-1_XXXXXXX",
        cognito_app_client_id="YYYYYYYYYYYY",
        sync_interval_seconds=300,  # Sync every 5 minutes
    )
    
    # Configure quit action to sync on exit
    config.quit_action = lambda: renpy_cloud.sync_on_quit()


# Login screen
screen login_screen():
    modal True
    
    frame:
        xalign 0.5
        yalign 0.5
        xsize 600
        ysize 400
        
        vbox:
            spacing 20
            xalign 0.5
            yalign 0.5
            
            text "Cloud Save Login" size 30 xalign 0.5
            
            if login_error:
                text "[login_error]" color "#ff0000" xalign 0.5
            
            hbox:
                spacing 10
                text "Username:" yalign 0.5
                input default "" value VariableInputValue("username") length 30
            
            hbox:
                spacing 10
                text "Password:" yalign 0.5
                input default "" value VariableInputValue("password") length 30 copypaste False
            
            hbox:
                spacing 20
                xalign 0.5
                
                textbutton "Login" action Function(do_login)
                textbutton "Sign Up" action Jump("signup_label")
                textbutton "Skip" action Jump("start_game")


screen signup_screen():
    modal True
    
    frame:
        xalign 0.5
        yalign 0.5
        xsize 600
        ysize 450
        
        vbox:
            spacing 20
            xalign 0.5
            yalign 0.5
            
            text "Create Account" size 30 xalign 0.5
            
            if signup_error:
                text "[signup_error]" color "#ff0000" xalign 0.5
            
            hbox:
                spacing 10
                text "Username:" yalign 0.5
                input default "" value VariableInputValue("signup_username") length 30
            
            hbox:
                spacing 10
                text "Email:" yalign 0.5
                input default "" value VariableInputValue("signup_email") length 50
            
            hbox:
                spacing 10
                text "Password:" yalign 0.5
                input default "" value VariableInputValue("signup_password") length 30 copypaste False
            
            hbox:
                spacing 20
                xalign 0.5
                
                textbutton "Create Account" action Function(do_signup)
                textbutton "Back to Login" action Jump("login_label")


# Cloud sync status screen
screen cloud_status():
    frame:
        xalign 1.0
        yalign 0.0
        xsize 250
        
        vbox:
            spacing 10
            
            if renpy_cloud.is_authenticated():
                text "☁ Cloud: Connected" color "#00ff00"
                textbutton "Force Sync" action Function(do_force_sync)
                textbutton "Logout" action Function(do_logout)
            else:
                text "☁ Cloud: Offline" color "#888888"
                textbutton "Login" action Jump("login_label")


# Python functions for cloud operations
init python:
    username = ""
    password = ""
    login_error = ""
    
    signup_username = ""
    signup_email = ""
    signup_password = ""
    signup_error = ""
    
    def do_login():
        global login_error
        try:
            if renpy_cloud.login(username, password):
                renpy.notify("Logged in successfully!")
                login_error = ""
                renpy.jump("start_game")
        except renpy_cloud.AuthenticationError as e:
            login_error = str(e)
            renpy.notify(f"Login failed: {e}")
    
    def do_signup():
        global signup_error
        try:
            renpy_cloud.signup(signup_username, signup_password, signup_email)
            renpy.notify("Account created! Check your email to verify.")
            signup_error = ""
            renpy.jump("login_label")
        except renpy_cloud.AuthenticationError as e:
            signup_error = str(e)
            renpy.notify(f"Signup failed: {e}")
    
    def do_logout():
        renpy_cloud.logout()
        renpy.notify("Logged out")
    
    def do_force_sync():
        if renpy_cloud.force_sync():
            renpy.notify("Sync completed!")
        else:
            renpy.notify("Sync failed or not authenticated")


# Game start
label start:
    # Perform initial sync (respects throttling)
    python:
        renpy_cloud.sync_on_start()
    
    # Show cloud status
    show screen cloud_status
    
    jump start_game


label login_label:
    call screen login_screen
    return


label signup_label:
    call screen signup_screen
    return


label start_game:
    scene bg room
    
    e "Welcome to the renpy-cloud example game!"
    
    e "This game demonstrates cloud save synchronization."
    
    menu:
        "What would you like to learn about?"
        
        "How cloud sync works":
            e "Cloud sync automatically saves your progress to the cloud."
            e "It syncs your persistent data and the most recent save slot."
            e "Syncs happen every 5 minutes, and always when you quit."
        
        "How to enable cloud saves":
            e "If you're logged in, cloud saves are automatic!"
            e "Your saves will sync across all your devices."
            e "You can also force a sync anytime from the cloud status panel."
        
        "Privacy and security":
            e "Your saves are encrypted in transit and stored securely in AWS S3."
            e "Each user's saves are completely isolated."
            e "No AWS credentials are ever stored on your device."
    
    e "Let's test the save system. I'll set a persistent variable."
    
    python:
        persistent.example_counter = getattr(persistent, 'example_counter', 0) + 1
    
    e "This is visit number [persistent.example_counter]!"
    
    e "If you log in and sync, this counter will be preserved across devices."
    
    menu:
        "What would you like to do?"
        
        "Force sync now":
            python:
                if renpy_cloud.is_authenticated():
                    if renpy_cloud.force_sync():
                        renpy.notify("Sync completed!")
                    else:
                        renpy.notify("Sync failed")
                else:
                    renpy.notify("Please log in first")
            
            e "Sync request sent!"
        
        "Continue playing":
            pass
    
    e "Thanks for trying the renpy-cloud example!"
    
    e "Remember: your saves will automatically sync if you're logged in."
    
    return

