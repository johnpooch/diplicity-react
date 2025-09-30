import { Avatar, AvatarProps, Badge } from '@mui/material';

import { Flags } from '../assets/flags';
import { MemberRead } from '../store/service';

const AVATAR_SIZE = {
    small: 24,
    medium: 32,
}

const BADGE_SIZE = {
    small: 16,
    medium: 24,
}

const BORDER_SIZE = {
    small: 1,
    medium: 2,
}

type MemberAvatarProps = Pick<AvatarProps, 'key'> & {
    size: "small" | "medium";
    variant: string;
    member: MemberRead;
}

const MemberAvatar: React.FC<MemberAvatarProps> = ({ variant, member, size, ...rest }) => {

    const avatarSize = AVATAR_SIZE[size];
    const badgeSize = BADGE_SIZE[size];
    const borderSize = BORDER_SIZE[size];

    const mainAvatar = (
        <Avatar
            {...rest}
            src={member.picture}
            sx={{ width: avatarSize, height: avatarSize }}
        />
    );

    // If no nation flag, just return the avatar
    if (!member.nation) {
        return mainAvatar;
    }

    const nationFlag = Flags[variant as keyof typeof Flags]?.[member.nation.toLowerCase() as keyof typeof Flags[keyof typeof Flags]];

    // Otherwise, wrap it with the Badge
    return (
        <Badge
            overlap="circular"
            anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
            badgeContent={
                <Avatar
                    src={nationFlag}
                    sx={{
                        width: badgeSize,
                        height: badgeSize,
                        border: `${borderSize}px solid white`,
                    }}
                />
            }
        >
            {mainAvatar}
        </Badge>
    );
}

export { MemberAvatar };