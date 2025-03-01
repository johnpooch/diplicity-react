import React from "react";
import { Button, Typography, Box, Stack, Avatar, Link, Alert } from "@mui/material";

const getLoginUrl = (): string => {
  const redirectUrl = location.href;
  const tokenDuration = 60 * 60 * 24 * 365 * 100;
  return `https://diplicity-engine.appspot.com/Auth/Login?redirect-to=${encodeURI(
    redirectUrl
  )}&token-duration=${tokenDuration}`;
};

const styles: Styles = {
  root: {
    display: "flex",
    flexDirection: "column",
  },
  heroSection: {
    display: "flex",
    minHeight: "100vh",
  },
  contentContainer: {
    width: "50%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: 4,
  },
  imageContainer: {
    width: "50%",
    height: "100vh",
    overflow: "hidden",
    position: "relative",
  },
  backgroundImage: {
    position: "absolute",
    height: "100%",
    width: "auto",
    left: 0,
    objectFit: "cover",
  },
  buttonContainer: {
    display: "flex",
    gap: 2,
    mt: 4,
  },
  loginSection: {
    display: "flex",
    justifyContent: "left",
    alignItems: "center",
    minHeight: "100vh",
    width: "100%",
  },
  contentSection: {
    width: "100%",
    maxWidth: "1000px",
    padding: 4,
    bgcolor: "background.paper",
    margin: "0 auto",  // Centers the content horizontally
  },
  contentRow: {
    display: "grid",
    gridTemplateColumns: {
      xs: "1fr",
      md: "1fr 1fr",
    },
    gap: 4,
    mb: 6,
  },
  exampleImage: {
    width: 200,
    height: 200,
    bgcolor: "grey.300",
    mb: 2,
  },
  stack: (theme) => ({
    padding: 4,
    bgcolor: theme.palette.background.paper,
    borderRadius: "4px",
  }),
  logo: {
    height: 48,
    width: 48,
  },
  title: {
    variant: "h1",
    component: "div",
    align: "left",
  },
  subtitle: {
    variant: "body1",
  },
};

const Login: React.FC = () => {
  const onClickLogin = () => {
    const loginUrl = getLoginUrl();
    if (window) {
      window.open(loginUrl, "_self");
    }
  };

  const scrollToHowToPlay = (event: React.MouseEvent) => {
    event.preventDefault();
    document.getElementById('how-to-play')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <Box sx={styles.root}>
      <Box sx={styles.heroSection}>
        <Box sx={styles.contentContainer}>
          <Stack spacing={3} maxWidth="600px">
            <Typography variant="h3" component="h1">
              First destroy your enemies.<br/>Then destroy your friends.
            </Typography>
            <Typography variant="body1">
              Diplicity is a digital adaptation of the board game of Diplomacy
            </Typography>
            <Box sx={styles.buttonContainer}>
              <Button variant="outlined" color="primary" onClick={scrollToHowToPlay}>
                Learn how to play
              </Button>
              <Button variant="contained" color="primary" onClick={onClickLogin}>
                Log in with Google
              </Button>
            </Box>
          </Stack>
        </Box>
        <Box sx={styles.imageContainer}>
          <Box
            component="img"
           // src="/src/static/img/login_background.jpg"
           src="/src/static/img/login_intro.png"
            sx={styles.backgroundImage}
            alt="Background"
          />
        </Box>
      </Box>

      <Box sx={styles.contentSection}>
        <Box sx={styles.contentRow} id="how-to-play">
          <Box>
            <Typography variant="h5" gutterBottom>
              How to Play
            </Typography>
            <Typography variant="body1">
              You command your units, battling for supply centers — control more than half to win.<br /><br />
              But victory requires allies, so balance military tactics with careful diplomacy. 
              Each turn, players negotiate, forge alliances, and submit secret orders.
            </Typography>
          </Box>
          <Alert severity="warning" sx={{ height: 'fit-content' }}>
            Diplomacy is a slow game of real-life negotiation. 
            It's about real chats with players that have busy lives, so one turn usually lasts a day or more. 
            Be prepared for a time commitment before any military action unfolds.
          </Alert>
        </Box>
        {/* Supply Centers */}
        <Box sx={styles.contentRow}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Supply Centers
            </Typography>
            <Typography variant="body1">
              Supply centers are the key to victory. Each one lets you build another unit, 
              and controlling more than half of them wins you the game.
            </Typography>
          </Box>
          <Box>
            <Box sx={styles.exampleImage} component="img" src="/placeholder-sc.png" alt="Supply Center Example" />
            <Typography variant="caption" gutterBottom>Supply Center Example</Typography>
          </Box>
        </Box>
        {/* Rest of the sections remain the same... */}
      {/* Units Section */}
      <Box sx={styles.contentRow}>
        <Box>
          <Typography variant="h6" gutterBottom>
            Units
          </Typography>
          <Typography variant="body1">
            Only one unit can occupy a province and all units are equally strong. So, to attack and force retreats, 
            you need support from other units. Players control Armies (only move on land) and Fleets 
            (move on sea and coastal provinces).
          </Typography>
        </Box>
        <Box>
          <Box sx={styles.exampleImage} component="img" src="/placeholder-units.png" alt="Units Example" />
          <Typography variant="caption" gutterBottom>Units Example</Typography>
        </Box>
      </Box>
      
      {/* Continue this pattern for each section */}
      <Box sx={styles.contentRow}>
        <Box>
          <Typography variant="h6" gutterBottom>
            Basic Orders
          </Typography>
          <Typography variant="body1">
            On its own, a unit can either defend (hold) or attack (move). 
            Fleets can also transport armies over water (convoy).
          </Typography>
        </Box>
        <Box>
          <Box sx={styles.exampleImage} component="img" src="/placeholder-orders.png" alt="Basic Orders Example" />
          <Typography variant="caption" gutterBottom>Basic Orders Example</Typography>
        </Box>
      </Box>
      
      {/* Continue with the same pattern for remaining sections... */}
    </Box>      </Box>

  );
};

export { Login };
